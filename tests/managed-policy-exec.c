#define _GNU_SOURCE
#include <assert.h>
#include <grp.h>
#include <sys/prctl.h>
#include "wx-policy.h"

int main(int argc, char **argv) {
    assert(argc > 1 && getuid() == 0);
    assert(setgroups(0, NULL) == 0 && setgid(1000) == 0 && setuid(1000) == 0);
    assert(prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0);
    assert(native_seccomp_install() == 0);
    execv(argv[1], argv + 1);
    return 127;
}
