/* Enclave OS runtime filter for native little-endian x86-64 and RV64.
 * Derived from the pinned platform filter in reference/. The syscall ABI is
 * selected at compile time; all original denials and errno semantics remain.
 * Install only after privilege drop and PR_SET_NO_NEW_PRIVS, before exec.
 */
#ifndef ENCLAVE_APP_SECCOMP_H
#define ENCLAVE_APP_SECCOMP_H
#include <stdio.h>
#include "sha256-min.h"
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error Unsupported byte order
#endif
#if defined(__x86_64__) && !defined(__ILP32__)
#define APP_AUDIT_ARCH_NATIVE 0xC000003EU
#elif defined(__riscv) && __riscv_xlen == 64
#define APP_AUDIT_ARCH_NATIVE 0xC00000F3U
#else
#error Unsupported runtime syscall ABI
#endif

/* the kernel's BPF and seccomp ABI (linux/filter.h, linux/seccomp.h, linux/audit.h) */
struct app_sock_filter { uint16_t code; uint8_t jt, jf; uint32_t k; };
struct app_sock_fprog { unsigned short len; struct app_sock_filter *filter; };
#define APP_BPF_LD_W_ABS 0x20              /* BPF_LD | BPF_W | BPF_ABS */
#define APP_BPF_JEQ_K 0x15                 /* BPF_JMP | BPF_JEQ | BPF_K */
#define APP_BPF_JGE_K 0x35                 /* BPF_JMP | BPF_JGE | BPF_K */
#define APP_BPF_JSET_K 0x45                /* BPF_JMP | BPF_JSET | BPF_K */
#define APP_BPF_RET_K 0x06                 /* BPF_RET | BPF_K */
#define APP_SECCOMP_MODE_FILTER 2
#define APP_RET_KILL_PROCESS 0x80000000U
#define APP_RET_ERRNO 0x00050000U
#define APP_RET_ALLOW 0x7fff0000U
#define APP_EPERM (APP_RET_ERRNO | (EPERM & 0xffff))
#define APP_ENOSYS (APP_RET_ERRNO | (ENOSYS & 0xffff))
#define APP_AUDIT_ARCH_X86_64 0xC000003EU
#define APP_X32_BIT 0x40000000U
#define APP_OFF_NR 0                       /* struct seccomp_data: nr, arch, instruction_pointer, args[6] */
#define APP_OFF_ARCH 4
#define APP_OFF_ARG0_LO 16                 /* little-endian: args[0]'s low 32 bits */
#define APP_AF_VSOCK 40
#define APP_CLONE_NEW_CLONE 0x7E020000U    /* NEWNS|NEWCGROUP|NEWUTS|NEWIPC|NEWUSER|NEWPID|NEWNET (clone's low byte is the exit signal) */
#define APP_CLONE_NEW_UNSHARE 0x7E020080U  /* ...and NEWTIME, for unshare */

/* Native libc syscall constants; do not reuse another ISA's numeric table. */
#define APP_NR_socket SYS_socket
#define APP_NR_socketpair SYS_socketpair
#define APP_NR_clone SYS_clone
#define APP_NR_ptrace SYS_ptrace
#define APP_NR_init_module SYS_init_module
#define APP_NR_delete_module SYS_delete_module
#define APP_NR_kexec_load SYS_kexec_load
#define APP_NR_add_key SYS_add_key
#define APP_NR_request_key SYS_request_key
#define APP_NR_keyctl SYS_keyctl
#define APP_NR_unshare SYS_unshare
#define APP_NR_perf_event_open SYS_perf_event_open
#define APP_NR_setns SYS_setns
#define APP_NR_kcmp SYS_kcmp
#define APP_NR_process_vm_readv SYS_process_vm_readv
#define APP_NR_process_vm_writev SYS_process_vm_writev
#define APP_NR_finit_module SYS_finit_module
#define APP_NR_kexec_file_load SYS_kexec_file_load
#define APP_NR_bpf SYS_bpf
#define APP_NR_userfaultfd SYS_userfaultfd
#define APP_NR_io_uring_setup SYS_io_uring_setup
#define APP_NR_io_uring_enter SYS_io_uring_enter
#define APP_NR_io_uring_register SYS_io_uring_register
#define APP_NR_clone3 SYS_clone3
#define APP_NR_pidfd_getfd SYS_pidfd_getfd
#define APP_NR_process_madvise SYS_process_madvise

#define APP_STMT(code, k) {(code), 0, 0, (k)}
#define APP_JUMP(code, k, jt, jf) {(code), (jt), (jf), (k)}
/* nr == N -> return ACTION (A still holds nr afterwards for the next rule) */
#define APP_RULE(nr, action) APP_JUMP(APP_BPF_JEQ_K, (nr), 0, 1), APP_STMT(APP_BPF_RET_K, (action))
/* nr == N and (the low word of arg 0 TEST K) -> return ACTION, else ALLOW; five instructions, skipped as a block */
#define APP_ARG0_EQ(nr, val, action) \
    APP_JUMP(APP_BPF_JEQ_K, (nr), 0, 4), APP_STMT(APP_BPF_LD_W_ABS, APP_OFF_ARG0_LO), \
    APP_JUMP(APP_BPF_JEQ_K, (val), 0, 1), APP_STMT(APP_BPF_RET_K, (action)), APP_STMT(APP_BPF_RET_K, APP_RET_ALLOW)
#define APP_ARG0_ANY(nr, mask, action) \
    APP_JUMP(APP_BPF_JEQ_K, (nr), 0, 4), APP_STMT(APP_BPF_LD_W_ABS, APP_OFF_ARG0_LO), \
    APP_JUMP(APP_BPF_JSET_K, (mask), 0, 1), APP_STMT(APP_BPF_RET_K, (action)), APP_STMT(APP_BPF_RET_K, APP_RET_ALLOW)

static struct app_sock_filter app_seccomp_prog[] = {
    APP_STMT(APP_BPF_LD_W_ABS, APP_OFF_ARCH),
    APP_JUMP(APP_BPF_JEQ_K, APP_AUDIT_ARCH_NATIVE, 1, 0),
    APP_STMT(APP_BPF_RET_K, APP_RET_KILL_PROCESS),
    APP_STMT(APP_BPF_LD_W_ABS, APP_OFF_NR),
#if defined(__x86_64__)
    APP_JUMP(APP_BPF_JGE_K, APP_X32_BIT, 0, 1),
    APP_STMT(APP_BPF_RET_K, APP_RET_KILL_PROCESS),
#endif
    APP_ARG0_EQ(APP_NR_socket, APP_AF_VSOCK, APP_EPERM),
    APP_ARG0_EQ(APP_NR_socketpair, APP_AF_VSOCK, APP_EPERM),
    APP_ARG0_ANY(APP_NR_clone, APP_CLONE_NEW_CLONE, APP_EPERM),
    APP_ARG0_ANY(APP_NR_unshare, APP_CLONE_NEW_UNSHARE, APP_EPERM),
    APP_RULE(APP_NR_clone3, APP_ENOSYS),
    APP_RULE(APP_NR_setns, APP_EPERM),
    APP_RULE(APP_NR_io_uring_setup, APP_EPERM),
    APP_RULE(APP_NR_io_uring_enter, APP_EPERM),
    APP_RULE(APP_NR_io_uring_register, APP_EPERM),
    APP_RULE(APP_NR_ptrace, APP_EPERM),
    APP_RULE(APP_NR_process_vm_readv, APP_EPERM),
    APP_RULE(APP_NR_process_vm_writev, APP_EPERM),
    APP_RULE(APP_NR_pidfd_getfd, APP_EPERM),
    APP_RULE(APP_NR_process_madvise, APP_EPERM),
    APP_RULE(APP_NR_kcmp, APP_EPERM),
    APP_RULE(APP_NR_bpf, APP_EPERM),
    APP_RULE(APP_NR_perf_event_open, APP_EPERM),
    APP_RULE(APP_NR_keyctl, APP_EPERM),
    APP_RULE(APP_NR_add_key, APP_EPERM),
    APP_RULE(APP_NR_request_key, APP_EPERM),
    APP_RULE(APP_NR_userfaultfd, APP_EPERM),
    APP_RULE(APP_NR_kexec_load, APP_RET_KILL_PROCESS),
    APP_RULE(APP_NR_kexec_file_load, APP_RET_KILL_PROCESS),
    APP_RULE(APP_NR_init_module, APP_RET_KILL_PROCESS),
    APP_RULE(APP_NR_finit_module, APP_RET_KILL_PROCESS),
    APP_RULE(APP_NR_delete_module, APP_RET_KILL_PROCESS),
    APP_STMT(APP_BPF_RET_K, APP_RET_ALLOW),
};

/* THE STATEMENT an init makes once this filter is installed on the runtime (enclave-87: positive evidence, not only the
 * absence of an error): the sha256 of the exact BPF program handed to the kernel - this sock_filter array, 8 bytes an
 * instruction on x86-64, the same bytes PTRACE_SECCOMP_GET_FILTER returns - and its length. The attester carries the hash
 * into the attested self-test (seccomp=<hash>); anyone can recompute it from this header. -> the line's length, or -1. */
#define APP_SECCOMP_RULES ((unsigned)(sizeof app_seccomp_prog / sizeof app_seccomp_prog[0]))
static int app_seccomp_statement(char *buf, size_t n) {
    char hex[65];
    sha256_min_hex(app_seccomp_prog, sizeof app_seccomp_prog, hex);
    int k = snprintf(buf, n, "seccomp sha256=%s rules=%u\n", hex, APP_SECCOMP_RULES);
    return k > 0 && (size_t)k < n ? k : -1;
}

/* needs PR_SET_NO_NEW_PRIVS already set (the caller's drop sets it); a filter cannot be removed once installed */
static int app_seccomp_install(void) {
    struct app_sock_fprog prog = {(unsigned short)(sizeof app_seccomp_prog / sizeof app_seccomp_prog[0]), app_seccomp_prog};
    if (prctl(PR_SET_SECCOMP, APP_SECCOMP_MODE_FILTER, &prog, 0, 0) != 0) return -1;
    if (prctl(PR_GET_SECCOMP, 0, 0, 0, 0) != APP_SECCOMP_MODE_FILTER) { errno = EPERM; return -1; }
    return 0;
}
#endif
