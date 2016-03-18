/*************************************************************************
 > File Name: server.c
 > Author: David Ding
 ************************************************************************/

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

#define SERVER_PORT 6000
#define BUFFER_SIZE 1024
#define FILE_NAME_MAX_SIZE 512

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

    if(getIfaceName(iface_name, sizeof(iface_name)) < 0) {
        printf("get interface name error!\n");
        return;
    }

    if(getIpAddress(iface_name, (char *) &intaddr, 15) < 0) {
        printf("get interface ip address error!\n");
        return;
    }
    
    strcpy( ipaddr, (char *) &intaddr );
}

int main()
{
    int ret = -1;
    int count = -1;
    char buffer[1024];
    char localip[50];
    fd_set readfd;
    struct sockaddr_in from_addr;
    socklen_t from_len = sizeof(struct sockaddr_in);
    struct timeval timeout;

    timeout.tv_sec = 2;
    timeout.tv_usec = 0;

     // define inetnet address
     struct sockaddr_in server_addr;
     bzero(&server_addr, sizeof(server_addr));
     server_addr.sin_family = AF_INET;
     server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
     server_addr.sin_port = htons(SERVER_PORT);

     // create a socket
     int sock = socket(AF_INET, SOCK_DGRAM, 0);
     if(sock == -1)
     {
          perror("Create Socket Failed:");
          exit(1);
     }

     // bind socket with the address
     if(-1 == (bind(sock,(struct sockaddr*)&server_addr,sizeof(server_addr))))
     {
          perror("Server Bind Failed:");
          exit(1);
     }

	GetLocalIpAddress( localip );

     // waiting for data
     while(1)
     {
        // reset
        FD_ZERO(&readfd);

        // set readfd to socket
        FD_SET(sock, &readfd);

        // select, detect any signs change
        ret = select(sock + 1, &readfd, NULL, NULL, &timeout);
        switch (ret)
        {
            case -1: // error
                perror("select error:");
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

                    // Verify password
                    //if ( Password is ok )
                    {
                        printf("Client IP: %s, Port: %d, Data: %s\n",
                            (char *)inet_ntoa(from_addr.sin_addr), ntohs(from_addr.sin_port), buffer );

                        // send data back to client
                        // strcpy( localip, "192.168.0.110");
						from_addr.sin_family = AF_INET;
						from_addr.sin_port = htons(SERVER_PORT);
                        count = sendto(sock, localip, strlen(localip), 0, (struct sockaddr*) &from_addr, from_len);
                    }
                }
                break;
        }
     }

     close(sock);
     return 0;
}
