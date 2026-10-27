#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/cursorfont.h>
#include <signal.h>
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <fcntl.h>
#include <sys/file.h>

static volatile sig_atomic_t running=1;
static unsigned errors=0;
static void stop(int sig){(void)sig;running=0;}
static int error(Display *d,XErrorEvent *e){(void)d;errors++;fprintf(stderr,"X error %u request %u\n",e->error_code,e->request_code);return 0;}
int main(int argc,char **argv){
 const char *status=argc>1?argv[1]:"/home/desktop/.cache/shield-cursor.json";
 char lockpath[512],temp[512];
 snprintf(lockpath,sizeof(lockpath),"%s.lock",status);
 snprintf(temp,sizeof(temp),"%s.tmp",status);
 int lockfd=open(lockpath,O_CREAT|O_RDWR|O_CLOEXEC,0600);
 if(lockfd<0||flock(lockfd,LOCK_EX|LOCK_NB)){fprintf(stderr,"Cursor owner already running or lock unavailable\n");return 4;}
 signal(SIGTERM,stop);signal(SIGINT,stop);XSetErrorHandler(error);
 Display *d=XOpenDisplay(NULL);if(!d)return 1;
 Window root=DefaultRootWindow(d);
 /* Keep the cursor resource AND its owning X connection alive. An xsetroot
  * invocation leaves the cursor referenced by root after its owner exits;
  * Xorg SECURITY then rejects XFixes reads while that client slot is empty.
  * Do not disable SECURITY or change any client authorization. */
 Cursor arrow=XCreateFontCursor(d,XC_left_ptr);
 unsigned long frames=0;
 while(running){
  /* Only root's default is repaired. Explicit app/game cursor shapes and
   * invisible cursors on their own windows retain normal X inheritance. */
  XDefineCursor(d,root,arrow);
  XSync(d,False);
  frames++;
  FILE *f=fopen(temp,"w");
  if(f){fprintf(f,"{\"pid\":%d,\"cursor\":%lu,\"frames\":%lu,\"xErrors\":%u,\"renderer\":\"sunshine-native\"}\n",getpid(),arrow,frames,errors);fclose(f);rename(temp,status);}
  struct timespec delay={0,100000000};nanosleep(&delay,NULL);
 }
 XFreeCursor(d,arrow);XCloseDisplay(d);unlink(status);close(lockfd);return errors?2:0;
}
