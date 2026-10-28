#define _GNU_SOURCE
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include "role-policy.h"
#include "udev-policy.h"

#define DENIED(expr) do { errno = 0; assert((expr) == -1 && errno == EPERM); } while (0)

static void capabilities(unsigned long long expected) {
    struct __user_cap_header_struct h = { .version = _LINUX_CAPABILITY_VERSION_3, .pid = 0 };
    struct __user_cap_data_struct d[2];
    assert(syscall(SYS_capget, &h, d) == 0);
    assert((((unsigned long long)d[1].effective << 32) | d[0].effective) == expected);
    assert((((unsigned long long)d[1].permitted << 32) | d[0].permitted) == expected);
    assert(d[0].inheritable == 0 && d[1].inheritable == 0);
    for (int cap = 0; cap < 64; ++cap) {
        int value = prctl(PR_CAPBSET_READ, cap, 0, 0, 0);
        if (value < 0) { assert(errno == EINVAL); break; }
        assert(value == (int)((expected >> cap) & 1));
        assert(prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_IS_SET, cap, 0, 0) == 0);
    }
    assert(prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0) == 1);
    assert(prctl(PR_GET_SECCOMP, 0, 0, 0, 0) == 2);
}

static void role(uid_t uid) {
    capabilities(0);
    uid_t r, e, s;
    gid_t gr, ge, gs;
    assert(getresuid(&r, &e, &s) == 0 && r == uid && e == uid && s == uid);
    gid_t gid = uid == 1001 ? 1000 : uid;
    assert(getresgid(&gr, &ge, &gs) == 0 && gr == gid && ge == gid && gs == gid);
    gid_t groups[2];
    int count = getgroups(2, groups);
    if (uid == 1001 || uid == 1003)
        assert(count == 1 && groups[0] == (uid == 1001 ? 1001 : 1000));
    else assert(count == 0);
    DENIED(setuid(0));
    DENIED(socket(AF_VSOCK, SOCK_STREAM, 0));
    DENIED(syscall(SYS_unshare, CLONE_NEWUSER));
}

static void udev(void) {
    assert(getuid() == 0 && geteuid() == 0);
    capabilities(UDEV_CAPS);
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    assert(fd >= 0 && close(fd) == 0);
    fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_KOBJECT_UEVENT);
    assert(fd >= 0);
    struct sockaddr_nl address = { .nl_family = AF_NETLINK, .nl_groups = 1 };
    assert(bind(fd, (struct sockaddr *)&address, sizeof address) == 0);
    assert(close(fd) == 0);
    DENIED(socket(AF_INET, SOCK_STREAM, 0));
    DENIED(socket(AF_VSOCK, SOCK_STREAM, 0));
    DENIED(socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE));
    DENIED(socket(AF_NETLINK, SOCK_RAW, NETLINK_NETFILTER));
    DENIED(syscall(SYS_ioctl, -1, 0, 0));
    DENIED(syscall(SYS_mknodat, -1, "invalid", 0, 0));
    DENIED(syscall(SYS_unshare, CLONE_NEWNET));
    DENIED(syscall(SYS_mount, 0, 0, 0, 0, 0));
    DENIED(syscall(SYS_io_uring_setup, 0, 0));
    assert(syscall(SYS_clone3, 0, 0) == -1 && errno == ENOSYS);
}

int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "udev")) { udev(); return 0; }
    if (argc == 3 && !strcmp(argv[1], "role")) { role((uid_t)atoi(argv[2])); return 0; }
    assert(argc == 1 && getuid() == 0);
    for (int identity = 999; identity <= 1003; ++identity) {
        pid_t child = fork();
        assert(child >= 0);
        if (!child) {
            if (identity == 999) {
                assert(udev_drop_capabilities() == 0 && udev_install_seccomp() == 0);
                udev();
                execl("/native-roles-test", "native-roles-test", "udev", NULL);
            } else {
                assert(native_enter_role((uid_t)identity) == 0);
                role((uid_t)identity);
                char uid[8];
                snprintf(uid, sizeof uid, "%d", identity);
                execl("/native-roles-test", "native-roles-test", "role", uid, NULL);
            }
            _exit(127);
        }
        int status;
        assert(waitpid(child, &status, 0) == child);
        assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
    }
    puts("ENCLAVE_NATIVE_ROLES_OK");
    return 0;
}
