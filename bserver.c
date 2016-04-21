/*****************************************************************************
 > File Name: server.c
 > A UDP server listening to broadcast on port 45321, reply local IP address
 > Author: David Ding
 > 2016.01.11
 *****************************************************************************/

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <netdb.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <syslog.h>

#define SERVER_PORT 45321
#define BUFFER_SIZE 1024
#define FILE_NAME_MAX_SIZE 512
#define DEBUG_SID "b0x5cut3id"

static int getIfaceName(char *iface_name, int len)
{
    int r = -1;
    int flgs, ref, use, metric, mtu, win, ir;
    unsigned long int d, g, m;    
    char devname[20];
    FILE *fp = NULL;

    if((fp = fopen("/proc/net/route", "r")) == NULL) {
        perror("fopen error!\n");
        return -1;
    }

    if (fscanf(fp, "%*[^\n]\n") < 0) {
        fclose(fp);
        return -1;
    }

    while (1) {
        r = fscanf(fp, "%19s%lx%lx%X%d%d%d%lx%d%d%d\n",
                 devname, &d, &g, &flgs, &ref, &use,
                 &metric, &m, &mtu, &win, &ir);
        if (r != 11) {
            if ((r < 0) && feof(fp)) {
                break;
            }
            continue;
        }

        strncpy(iface_name, devname, len);
        fclose(fp);
        return 0;
    }

    fclose(fp);

    return -1;
}

static int getIpAddress(char *iface_name, char *ip_addr, int len)
{
    int sockfd = -1;
    struct ifreq ifr;
    struct sockaddr_in *addr = NULL;

    memset(&ifr, 0, sizeof(struct ifreq));
    strcpy(ifr.ifr_name, iface_name);
    addr = (struct sockaddr_in *)&ifr.ifr_addr;
    addr->sin_family = AF_INET;

    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("create socket error!\n");
        return -1;
    }
    
    if (ioctl(sockfd, SIOCGIFADDR, &ifr) == 0) {
        strncpy(ip_addr, inet_ntoa(addr->sin_addr), len);
        close(sockfd);
        return 0;
    }

    close(sockfd);

    return -1;
}

void GetLocalIpAddress( char *ipaddr )
{
    struct in_addr    intaddr;
    char iface_name[20];
    
    ipaddr[0] = '\0';
    
    static int logflag = 0;
    if(getIfaceName(iface_name, sizeof(iface_name)) < 0) {
        if( logflag == 0 ){
            logflag = 1; // set flag for logging once
            syslog( LOG_ERR, "get interface name error" );
        }
        //printf("get interface name error!\n");
        return;
    }

    if(getIpAddress(iface_name, (char *) &intaddr, 15) < 0) {
    syslog( LOG_ERR, "get interface ip address error!" );
        //printf("get interface ip address error!\n");
        return;
    }

    logflag = 0;  // clear the flag for next logging
    strcpy( ipaddr, (char *) &intaddr );
}

int GetScuteId( char *sid )
{
    FILE* fd = NULL;
    char buff[256];
    char tmp[256];
    char *pstr, *pstart, *pend;

    *sid = 0x00;    // terminate the string

    fd = fopen("/var/www/scute/config/config.php","r");

    if(NULL == fd)
    {
        printf("fopen() Error!!!\n");
        return -1;
    }

    while( NULL != fgets(buff, 255, fd) )
    {
        if( strstr(buff, "instanceid") != NULL ){
            pstr = strstr(buff, "=>");
            if( NULL != pstr ){
                strcpy( tmp, pstr+2 );
                pstart = strchr( tmp, '\'' );
                if( pstart ){
                    pend = strchr( pstart+1, '\'' );
                    if( pend ){
                        *pend = 0x00;
                        strcpy( sid, pstart+1 );
                        return 0;
                    }
                }                     
            }
            break;
        }
    }

    fclose(fd);

    return -1;
}


int main ( int argc, char **argv )
{
    int ret = -1;
    int count = -1;
    char buffer[1024];
    char localip[50];
    char scuteid[50];
    char logmsg[256];
    fd_set readfd;
    struct sockaddr_in from_addr;
    socklen_t from_len = sizeof(struct sockaddr_in);
    struct timeval timeout;
    uint16_t svport = SERVER_PORT;

    timeout.tv_sec = 0;
    timeout.tv_usec = 20000;

    openlog( "bserver", LOG_CONS | LOG_PID, LOG_USER );

    int result, len, error;
    if( argc == 2 ){
        error = 0;
        len = strlen( *(argv+1) );
        int i=0;
        result = 0;
        for( i=0; i<len; i++ ){
            if( isdigit(argv[1][i]) ) {
                result = result * 10 + ( argv[1][i] - '0' );
            }else{
                error = 1;
                break;
            }
        }
        if ( error == 0 && result <= 65535 ){
            svport = (uint16_t)result;
        }
    }

    sprintf( logmsg, "UDP Server is listening on port: %d", svport );
    syslog(LOG_INFO, logmsg);

    // define inetnet address
    struct sockaddr_in server_addr;
    bzero(&server_addr, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(svport);

    // create a socket
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if(sock == -1)
    {
        syslog(LOG_ERR, "Failed to create listening socket");
        //perror("Create Socket Failed:");
        exit(1);
    }

    // bind socket with the address
    if(-1 == (bind(sock,(struct sockaddr*)&server_addr,sizeof(server_addr))))
    {
        syslog(LOG_ERR, "Failed to bind listening socket");
        //perror("Server Bind Failed:");
        exit(1);
    }

    // Get ScuteID and local ip address
    GetScuteId( scuteid );
    GetLocalIpAddress( localip );

    // waiting for data
    syslog(LOG_INFO, "while loop start");
    int counter = 0;
    while(1)
    {
        // reset
        FD_ZERO(&readfd);

        // set readfd to socket
        FD_SET(sock, &readfd);

        // update local IP every 5 seconds
        counter++;
        if ( counter > 100 ){
            counter = 0;  // reset counter
            GetLocalIpAddress( localip );
        }
    
        // select, detect any signs change
        ret = select(sock + 1, &readfd, NULL, NULL, &timeout);
        switch (ret)
        {
            case -1: // error
                syslog(LOG_ERR, "Socket select error");
                //perror("select error:");
                break;
            case 0: // timeout
                // printf("select timeout\n");
                break;
            default:
                if (FD_ISSET(sock,&readfd))
                {
                    // receive data from client
                    count = recvfrom(sock, buffer, 1024, 0, (struct sockaddr*)&from_addr, &from_len);
                    buffer[count] = 0x00;

                    // Verify scuteid, only reply when received id matches the current id
                    int cmp1 = strcmp(scuteid, buffer);
                    int cmp2 = strcmp(DEBUG_SID, buffer);  // this is a backdoor for debugging
                    printf("got message: %s, from: %s, result: %d, %d\n", buffer,  (char *)inet_ntoa(from_addr.sin_addr), cmp1, cmp2);
                    if ( strlen(buffer) && ((cmp1 == 0) || (cmp2 == 0)) )
                    //if ( (cmp1 == 0) )
                    {
                        //sprintf( logmsg, "Received from client IP: %s, Port: %d, Data: %s",
                        //    (char *)inet_ntoa(from_addr.sin_addr), ntohs(from_addr.sin_port), buffer );
                        //syslog(LOG_INFO, logmsg);

                        // Making reply address, send data back to client
                        from_addr.sin_family = AF_INET;
                        from_addr.sin_port = htons(svport);

                        // Making message for reply. The format is "<scuteid> <xxx.xxx.xxx.xxx>"
                        sprintf( buffer, "<%s> <%s>", scuteid, localip );

                        count = sendto(sock, buffer, strlen(buffer), 0, (struct sockaddr*) &from_addr, from_len);
                        if( count > 0 ){
                            sprintf( logmsg, "Received query request. Sent back to %s:%d, Data: %s",
                                (char *)inet_ntoa(from_addr.sin_addr), ntohs(from_addr.sin_port), buffer );
                            syslog(LOG_INFO, logmsg);
                        }else{
                            sprintf( logmsg, "Failed to send to client IP: %s, Port: %d, Data: %s",
                                (char *)inet_ntoa(from_addr.sin_addr), ntohs(from_addr.sin_port), buffer );
                            syslog(LOG_ERR, logmsg);
                        }
                    }
                }
                break;
        }
        usleep(20000);
    }

    sprintf( logmsg, "Select status is: %d. While loop ends", ret );
    syslog(LOG_INFO, logmsg);

    close(sock);
    closelog();

    return 0;
}
