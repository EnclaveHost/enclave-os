#include <X11/Xlib.h>
#include <X11/extensions/Xfixes.h>
#include <stdio.h>
static int errors=0;
static int onerror(Display *d,XErrorEvent *e){(void)d;(void)e;errors++;return 0;}
int main(void){
    XSetErrorHandler(onerror);
    Display *d=XOpenDisplay(NULL); if(!d)return 2;
    XFixesCursorImage *image=XFixesGetCursorImage(d); XSync(d,False);
    int ok=image && image->width && image->height && !errors;
    if(image)XFree(image); XCloseDisplay(d);
    return ok ? 0 : 1;
}
