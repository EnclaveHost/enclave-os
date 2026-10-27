#define _GNU_SOURCE
#include <assert.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/shm.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include "wx-policy.h"

#define denied(expression) do { \
    errno = 0; \
    long result = (expression); \
    if (result != -1 || errno != EPERM) { \
        fprintf(stderr, "denial failed: %s result=%ld errno=%d\n", #expression, result, errno); \
        abort(); \
    } \
} while (0)
static void protections(void) {
    void *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    assert(p != MAP_FAILED);
    *(volatile char *)p = 7;
    errno = 0;
    denied(syscall(SYS_mmap, NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
    /* musl translates anonymous mmap EPERM to ENOMEM. */
    assert(mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0) == MAP_FAILED);
    assert(errno == ENOMEM || errno == EPERM);
    denied(mprotect(p, 4096, PROT_READ | PROT_WRITE | PROT_EXEC));
    assert(*(volatile char *)p == 7);
    *(volatile char *)p = 9;
#ifdef SYS_pkey_mprotect
    denied(syscall(SYS_pkey_mprotect, p, 4096, PROT_READ | PROT_WRITE | PROT_EXEC, -1));
#endif
    assert(mprotect(p, 4096, PROT_READ | PROT_EXEC) == 0);
    assert(mprotect(p, 4096, PROT_READ | PROT_WRITE) == 0);
    assert(munmap(p, 4096) == 0);
    assert(syscall(SYS_personality, 0xffffffffUL) >= 0);
    denied(syscall(SYS_personality, NWX_READ_IMPLIES_EXEC));
    int id = shmget(IPC_PRIVATE, 4096, IPC_CREAT | 0700);
    assert(id >= 0);
    denied((long)shmat(id, NULL, SHM_EXEC));
    p = shmat(id, NULL, 0);
    assert(p != (void *)-1);
    assert(shmdt(p) == 0 && shmctl(id, IPC_RMID, NULL) == 0);
}
static void interfaces(void) {
    denied(socket(AF_VSOCK, SOCK_STREAM, 0));
    int pair[2];
    denied(socketpair(AF_VSOCK, SOCK_STREAM, 0, pair));
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, pair) == 0);
    close(pair[0]); close(pair[1]);
    denied(syscall(SYS_unshare, 0x10000000UL));
    denied(syscall(SYS_clone, 0x10000000UL | SIGCHLD, 0, 0, 0, 0));
    denied(syscall(SYS_setns, -1, 0));
    denied(syscall(SYS_ptrace, 0, 0, 0, 0));
    denied(syscall(SYS_bpf, 0, 0, 0));
    denied(syscall(SYS_io_uring_setup, 0, 0));
    denied(syscall(SYS_pidfd_getfd, -1, 0, 0));
    denied(syscall(SYS_process_vm_readv, getpid(), 0, 0, 0, 0, 0));
    denied(syscall(SYS_process_vm_writev, getpid(), 0, 0, 0, 0, 0));
    assert(syscall(SYS_clone3, 0, 0) == -1 && errno == ENOSYS);
    pid_t p = fork();
    assert(p >= 0);
    if (!p) { protections(); _exit(0); }
    int status;
    assert(waitpid(p, &status, 0) == p && WIFEXITED(status) && WEXITSTATUS(status) == 0);
}
static void kill_probe(void) { syscall(SYS_init_module, 0, 0, 0); _exit(99); }
#if defined(__x86_64__)
static void x32_probe(void) { syscall(SYS_getpid | APP_X32_BIT); _exit(99); }
#endif
static void run(void (*probe)(void), int signal_number) {
    fflush(NULL);
    pid_t p = fork(); assert(p >= 0);
    if (!p) {
        assert(setgid(1000) == 0 && setuid(1000) == 0);
        assert(prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0);
        assert(native_seccomp_install() == 0);
        probe();
        _exit(0);
    }
    int status;
    assert(waitpid(p, &status, 0) == p);
    if (signal_number) assert(WIFSIGNALED(status) && WTERMSIG(status) == signal_number);
    else assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
}
int main(void) {
    char statement[128];
    assert(native_seccomp_statement(statement, sizeof statement) > 0);
    fputs(statement, stdout);
    run(protections, 0);
    run(interfaces, 0);
    run(kill_probe, SIGSYS);
#if defined(__x86_64__)
    run(x32_probe, SIGSYS);
#endif
    puts("ENCLAVE_POLICY_OK");
    return 0;
}
