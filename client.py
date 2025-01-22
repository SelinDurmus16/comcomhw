import socket
#Selin Durmus 150220771 
#After running server.py, in terminal, you will be asked:
#File name, error rate, window size

def main():
    #Client settings
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 12345

    #Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        #step 1: Request filename from server
        client_socket.sendto("REQUEST_FILENAME".encode('utf-8'), (SERVER_HOST, SERVER_PORT))
        filename, _ = client_socket.recvfrom(1024)
        filename = filename.decode('utf-8')
        print(f"Server provided filename: {filename}")

        #Acknowledge filename
        client_socket.sendto("ACK:Filename".encode('utf-8'), (SERVER_HOST, SERVER_PORT))

        #Step 2: Reliable Data Transfer
        received_data = {}
        expected_seq_num = 0

        while True:
            data, _ = client_socket.recvfrom(1024)
            packet_parts = data.decode('utf-8').split("|")
            packet_type = packet_parts[0]

            if packet_type == "2":  # Data packet
                seq_num = int(packet_parts[1])
                payload = packet_parts[2]
                print(f"Received packet {seq_num}: {payload}")

                # Store all received packets (even out-of-order ones)
                if seq_num >= expected_seq_num:
                    received_data[seq_num] = payload  # Store the packet
                    print(f"Stored packet {seq_num}")

                # Always send ACK for received packets
                ack_packet = f"1|{seq_num}".encode('utf-8')
                client_socket.sendto(ack_packet, (SERVER_HOST, SERVER_PORT))
                print(f"Sent ACK for packet {seq_num}")

            elif packet_type == "3":  # FIN packet
                print("Received FIN packet from server. Sending ACK for FIN.")

                # Send ACK for the server's FIN
                fin_ack_packet = f"1|{expected_seq_num + 1}".encode('utf-8')  # Acknowledge server's FIN
                client_socket.sendto(fin_ack_packet, (SERVER_HOST, SERVER_PORT))
                print("Sent ACK for server's FIN.")

                # Send the client's FIN packet
                fin_packet = f"3|{expected_seq_num + 2}".encode('utf-8')  # FIN packet
                client_socket.sendto(fin_packet, (SERVER_HOST, SERVER_PORT))
                print("Sent FIN packet to server.")
                break

        #Write received data to a file
        with open("received_file.txt", "w") as file:
            for i in sorted(received_data.keys()):
                file.write(received_data[i] + "\n")

    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
