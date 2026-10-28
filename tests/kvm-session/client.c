/* Disposable KVM test client. Never installed in a production platform. */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
int main(int argc,char **argv){
 if(argc!=4||getuid()!=0)return 64;
 int pid=atoi(argv[1]),uid=atoi(argv[2]);
 if(pid<2||(uid!=5001&&uid!=1000&&uid!=1001&&uid!=1002&&uid!=1003))return 64;
 if(strcmp(argv[3],"status")&&strcmp(argv[3],"start")&&strcmp(argv[3],"stop"))return 64;
 char path[80];snprintf(path,sizeof path,"/proc/%d/ns/net",pid);
 int n=open(path,O_RDONLY|O_CLOEXEC);if(n<0||setns(n,CLONE_NEWNET))return 65;close(n);
 if(setgroups(0,NULL)||setgid(uid)||setuid(uid))return 66;
 int fd=socket(AF_INET,SOCK_STREAM|SOCK_CLOEXEC,0);if(fd<0)return 67;
 struct timeval timeout={.tv_sec=2};setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof timeout);setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof timeout);
 struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(19080)};inet_pton(AF_INET,"127.0.0.1",&a.sin_addr);
 if(connect(fd,(struct sockaddr*)&a,sizeof a)){close(fd);return 70;}
 char req[256];int len=snprintf(req,sizeof req,"%s /v1/%s HTTP/1.1\r\nHost: localhost\r\nX-KVM-Box-Request: 1\r\nConnection: close\r\nContent-Length: 0\r\n\r\n",!strcmp(argv[3],"status")?"GET":"POST",argv[3]);
 if(write(fd,req,(size_t)len)!=len)return 71;
 char response[16384];size_t used=0;ssize_t got;
 while(used<sizeof(response)-1&&(got=read(fd,response+used,sizeof(response)-1-used))>0)used+=(size_t)got;
 close(fd);response[used]=0;
 if(strncmp(response,"HTTP/1.1 200 ",13)) {fprintf(stderr,"bad HTTP status\n");return 72;}
 char *body=strstr(response,"\r\n\r\n");if(!body)return 73;
 puts(body+4);return 0;
}
