#include "lwip/sockets.h"

int server_sock = -1;
struct sockaddr_in server_addr;
socklen_t server_addr_len = sizeof(server_addr);
