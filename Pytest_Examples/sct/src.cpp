#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <cstring>

int main()  
{
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in my_addr;  
    bzero(&my_addr, sizeof(my_addr));
    my_addr.sin_family = AF_INET;
    my_addr.sin_port = htons(11111);
    my_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    
    unsigned retry_times = 0;
    while(retry_times < 3)
    {
        if(bind(sockfd, (struct sockaddr*)&my_addr, sizeof(my_addr)) == 0)
        {
            break;
        }
        sleep(1000);
        ++retry_times;
    }
    listen(sockfd, 1);

    struct sockaddr_in client_addr;              
    socklen_t addr_len = sizeof(client_addr);        
    int connfd = accept(sockfd, (struct sockaddr*)&client_addr, &addr_len);

    while(true)  
    {
        char recv_buf[512] = "";
        unsigned int len = recv(connfd, recv_buf, sizeof(recv_buf), 0);
        if(len == 0)
        {
            break;
        }
        send(connfd, recv_buf, len, 0);
    }

    close(connfd);
    close(sockfd);
}
