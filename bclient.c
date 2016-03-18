//**************************************************************************************
// Example code to send broadcast message for asking ScuteBox ip address
// 
// Author: David Ding
// Date:   2016.02.01
//**************************************************************************************

#include<stdio.h>  
#include<stdlib.h>  
#include<string.h>  
#include<sys/socket.h>  
#include<sys/types.h>  
#include<unistd.h>  
#include<netinet/in.h>  
#include <errno.h>    

#define PORT 6000  

int main(int argc,char **argv)  
{  
    int sockfd;  
    int addrlen, slen, n;  
    struct sockaddr_in addr_ser;  
    char recvline[200], sendline[200];  
      
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);  
    if(sockfd == -1) {  
        printf("socket error:%s\n", strerror(errno));  
        return -1;  
    }
    int yes = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &yes, sizeof(yes));
      
    bzero(&addr_ser, sizeof(addr_ser));  
    addr_ser.sin_family = AF_INET;  
    addr_ser.sin_addr.s_addr = htonl(INADDR_BROADCAST);  
    addr_ser.sin_port = htons(PORT);  
      
    addrlen=sizeof(addr_ser);  

    //*********************************************************     
    // Create a socket for listening response from ScuteBox
    //*********************************************************      
    int recvfd;  
    struct sockaddr_in addr_rcv;  

    recvfd = socket(AF_INET, SOCK_DGRAM, 0);  
    if(recvfd == -1){  
        printf("socket error:%s\n", strerror(errno));  
        close( recvfd );
        close( sockfd );
        return -1;  
    }
    bzero(&addr_rcv, sizeof(addr_rcv));  
    addr_rcv.sin_family = AF_INET;  
    addr_rcv.sin_addr.s_addr = htonl(INADDR_ANY);  
    addr_rcv.sin_port = htons(PORT);       
    int err = bind(recvfd, (struct sockaddr *)&addr_rcv, sizeof(addr_rcv));  
    if(err==-1) {  
        printf("bind error:%s\n",strerror(errno));  
        close( recvfd );
        close( sockfd );
        return -1;  
    }  
    //**************************************************************      

    // sending 5 times, just in case
    int cnt = 5;
    while( cnt-- > 0)  
    {  
        // Sending encrypt message to SucteBox, here is dummy string 
        strcpy(sendline, "Dummy string for getting SucteBox message");  
          
        n = sendto(sockfd, sendline, strlen( sendline ), 0, (struct sockaddr *)&addr_ser, addrlen);  
        if(n == -1) {  
            printf("sendto error:%s\n",strerror(errno));  
            close( recvfd );
            close( sockfd );
            return -1;  
        }
    }  
          
    printf("Messagte Sent -> %s,   waiting for server...\n");
    while( 1 )
    {
        n = recvfrom(recvfd, recvline, 200, 0, (struct sockaddr *)&addr_rcv, &addrlen);
        if(n == -1) {
            printf("recvfrom error:%s\n",strerror(errno));
            break;
        }

        recvline[ n ] = '\0';
        if ( strcmp(sendline, recvline) != 0 ){
            printf("Message Received -> %s\n", recvline);  
            break;
        }else{
            // printf("********** ignore echo ***********\n");  
        }
    }
    
    close( recvfd );
    close( sockfd );
      
    return 0;  
}  

