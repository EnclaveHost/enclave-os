/* Disposable Hyper-V fixture layered over the production platform archive. The
 * production initializer is not bypassed or edited: rdinit explicitly selects
 * this distinct fixture, which invokes the production storage helper before
 * exercising the actual monitor/domain implementation with its test client. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <net/if.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <unistd.h>
#define CHECK(x) do { if (!(x)) { dprintf(2,"COMBINED_BOOT_FAIL line=%d errno=%d\n",__LINE__,errno); return 1; } } while (0)
static int run_cmd(char *const argv[]) {
    pid_t p=fork(); if(p<0)return -1;
    if(!p){char *const env[]={"PATH=/plat","HOME=/tmp",NULL};execve(argv[0],argv,env);_exit(127);}
    int status;pid_t got;do{got=waitpid(p,&status,0);}while(got<0&&errno==EINTR);
    return got==p && WIFEXITED(status) ? WEXITSTATUS(status) : -1;
}
static int run(void) {
    struct utsname k; CHECK(getpid()==1 && getuid()==0 && !uname(&k) && !strcmp(k.release,"6.6.87.2-enclave-kvm-box"));
    CHECK(!mount("devtmpfs","/dev","devtmpfs",MS_NOSUID,NULL));
    CHECK(!mount("proc","/proc","proc",MS_NOSUID|MS_NODEV|MS_NOEXEC,"hidepid=2"));
    CHECK(!mount("sysfs","/sys","sysfs",MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC,NULL));
    CHECK(!mount("tmpfs","/run","tmpfs",MS_NOSUID|MS_NODEV,"mode=0755,size=32m"));
    CHECK(!mount("tmpfs","/tmp","tmpfs",MS_NOSUID|MS_NODEV,"mode=1777,size=64m"));
    CHECK(!mount("cgroup2","/sys/fs/cgroup","cgroup2",MS_NOSUID|MS_NODEV|MS_NOEXEC,NULL));
    int fd=open("/sys/fs/cgroup/cgroup.subtree_control",O_WRONLY|O_CLOEXEC);CHECK(fd>=0);
    static const char req[]="+cpu +memory +pids";CHECK(write(fd,req,sizeof req-1)==sizeof req-1);close(fd);
    struct ifreq ifr={0};strcpy(ifr.ifr_name,"lo");fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);CHECK(fd>=0);
    CHECK(!ioctl(fd,SIOCGIFFLAGS,&ifr));ifr.ifr_flags|=IFF_UP;CHECK(!ioctl(fd,SIOCSIFFLAGS,&ifr));close(fd);
    char *const helper[]={"/plat/native-boot",NULL};CHECK(!run_cmd(helper));
    char *const probe[]={"/monitor-probe","-test.v","-test.run=^TestNativeGuestKVM$","-test.timeout=180s",NULL};
    CHECK(!run_cmd(probe));return 0;
}
int main(void) {int r=run();dprintf(1,"NATIVE_MONITOR_EXIT=%d\n",r);sync();reboot(RB_POWER_OFF);return r;}
