#!/bin/bash

# Note: This script is used for the V8 RISCV Developers.
#       You may need to modify some folders to fit your need.

set -e

while getopts ":j:" opt; do
  case ${opt} in
    j)
      NPROC=$OPTARG
      ;;
    \?)
      echo "Unknown option: $OPTARG" 1>&2
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      exit 2
      ;;
  esac
done
shift $((OPTIND -1))

# Config: modify it if you don't like the default path.
# IMPORTANT: please assert there is no space in pwd folder, or the script may
#            does undefined behaviors.
[ -z "$V8_ROOT" ] && V8_ROOT="$PWD"
[ -z "$RV_HOME" ] && RV_HOME="$HOME/opt/riscv"
[ -z "$NPROC"   ] && NPROC=`nproc`

# NOTE: This script supposes you could build a sim build successfully.
#       which means the depot_tools and other prebuilt binary blobs v8 need were ready.

echo "Now we are going to download and build RISC-V GNU toolchain and QEMU."
echo "A few repos and files will be downloaded at $PWD,"
echo "And the toolchain is going to be installed at $RV_HOME ."
echo "Press Ctrl-C if you do not like these configs, otherwise I will continue:"
read -p "You have 10s to cancel:" -t 10

# +++++++++++++++++++++++++++++++++++++++++
# RISC-V GNU Toolchain
# +++++++++++++++++++++++++++++++++++++++++

mkdir -p $RV_HOME

cd $V8_ROOT/
git clone https://github.com/riscv/riscv-gnu-toolchain
pushd riscv-gnu-toolchain
git submodule update --init --recursive
./configure --prefix=$RV_HOME
make linux -j ${NPROC} || make linux -j 1
popd


export PATH="$PATH:$RV_HOME/bin"
echo "export PATH=$PATH:$RV_HOME/bin" >> $HOME/.bashrc

echo "If you hit the 'no-riscv64-compiler-found' error, run this sed command:"
echo "sed -i 's,riscv64-linux-gnu,riscv64-unknown-linux-gnu,' \\"
echo "     $V8_ROOT/v8/build/toolchain/linux/BUILD.gn"

cat <<"EOT"
# Now you can cross build a native d8 for RISC-V:

cd $V8_ROOT/v8
gn gen out/riscv64.native.debug \
    --args='is_component_build=false
    is_debug=true target_cpu="riscv64"
    v8_target_cpu="riscv64" use_goma=false
    goma_dir="None"
    symbol_level = 0'
ninja -C out/riscv64.native.debug -j ${NPROC}

# Remove obj and gen files that not needed.
rm -rf out/riscv64.native.debug/obj
rm -rf out/riscv64.native.debug/gen
EOT

# +++++++++++++++++++++++++++++++++++++++++
# RISC-V QEMU
# +++++++++++++++++++++++++++++++++++++++++

cd $V8_ROOT/
git clone https://github.com/qemu/qemu.git
cd qemu
# NOTE: master branch breaks current fedora image
git checkout v5.0.0
git submodule update -r --init -f
./configure --target-list=riscv64-softmmu && make -j ${NPROC}

# optional.
#sudo make install

###########################################################
# Deploy the Fedora Developer Rawhide on QEMU/RISCV64
###########################################################

cd $V8_ROOT/
wget https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Developer-Rawhide-20191123.n.0-fw_payload-uboot-qemu-virt-smode.elf
wget https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Developer-Rawhide-20191123.n.0-sda.raw.xz
unxz -k Fedora-Developer-Rawhide-20191123.n.0-sda.raw.xz

cat <<"EOTT"
# NOTE: the default image size is relatively small.
#       If you want to have a larger disk space in QEMU. run:

sudo apt install libguestfs-tools -y

truncate -r Fedora-Developer-Rawhide-*.raw expanded.raw
truncate -s 60G expanded.raw

sudo virt-resize -v -x --expand /dev/sda4 Fedora-Developer-Rawhide-*.raw expanded.raw
sudo virt-filesystems --long -h --all -a expanded.raw
sudo virt-df -h -a expanded.raw
EOTT

echo "Congrats! Now we are ready to Start QEMU."
echo
echo "Open a new terminal (Tab) to start QEMU"
echo "copy these commands in the new terminal:"
echo
echo "export VER=20191123.n.0"
echo "$V8_ROOT/qemu/riscv64-softmmu/qemu-system-riscv64 \\"
echo "  -nographic \\"
echo "  -machine virt \\"
echo "  -smp 4 \\"
echo "  -m 4G \\"
echo "  -kernel Fedora-Developer-Rawhide-${VER}-fw_payload-uboot-qemu-virt-smode.elf \\"
echo "  -object rng-random,filename=/dev/urandom,id=rng0 \\"
echo "  -device virtio-rng-device,rng=rng0 \\"
echo "  -device virtio-blk-device,drive=hd0 \\"
echo "  -drive file=expanded.raw,format=raw,id=hd0 \\"
echo "  -device virtio-net-device,netdev=usernet \\"
echo "  -netdev user,id=usernet,hostfwd=tcp::3333-:22"
echo
echo "Tip: You can quit qemu by pressing 'Ctrl-a x' key sequence."
echo "Tip: fedora forbid root password login. Either upload your pubkey into"
echo "     ROOT/.ssh/authorized_keys or add 'PermitRootLogin=yes' in /etc/ssh/sshd_config"

cat <<"EOT"
# After you built native d8, you could run these commands to test your d8 in QEMU
# please note the 3333 port, it must match your QEMU setting above.
scp -r -P 3333 $V8_ROOT/v8/out/riscv64.native.debug root@localhost:~/
scp -r -P 3333 $V8_ROOT/v8/test                     root@localhost:~/
scp -r -P 3333 $V8_ROOT/v8/tools                    root@localhost:~/
scp -r -P 3333 $V8_ROOT/v8/v8-riscv-tools           root@localhost:~/
ssh -p 3333 root@localhost python2 ./v8-riscv-tools/test-riscv.sh \
    -o riscv64.native.debug 2>&1 | tee v8.build.test.log
EOT
