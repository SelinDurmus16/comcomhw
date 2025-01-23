import socket
import time
import random as rd
#Selin Durmus 150220771 
#Erblina Nivokazi 150200917
#After running server.py, in terminal, you will be asked:
#File name, error rate, window size

def unreliableSend(packet, sock, userIP, errRate):
    if errRate < rd.randint(0, 100):
        sock.sendto(packet, userIP)

def main():
    #Server settings
    HOST = '127.0.0.1'
    PORT = 12345

    #Ask for filename, error rate, and window size once
    valid_filename = input("Enter the valid filename (e.g., example.txt): ")
    errRate = int(input("Enter the error rate (1-100): "))
    window_size = int(input("Enter the window size (e.g., 10, 50, 100): "))

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print(f"Server is running on {HOST}:{PORT}")

    while True:
        print("\nWaiting for client connection...")

        #Step 1: Send filename to the client
        data, client_addr = server_socket.recvfrom(1024)
        if data.decode('utf-8') == "REQUEST_FILENAME":
            server_socket.sendto(valid_filename.encode('utf-8'), client_addr)
            print(f"Sent filename '{valid_filename}' to client.")

        #Step 2: Receive client acknowledgment
        ack, _ = server_socket.recvfrom(1024)
        if ack.decode('utf-8') != "ACK:Filename":
            print("Client did not acknowledge filename. Aborting...")
            continue

        print("Client acknowledged filename. Starting data transfer...")

        #Step 3: Reliable Data Transfer
        with open(valid_filename, "r") as file:
            lines = file.readlines()

        base = 0
        next_seq_num = 0
        window = {}
        acked = set()

        while base < len(lines):
            #Send packets within the window
            while next_seq_num < base + window_size and next_seq_num < len(lines):
                packet = f"2|{next_seq_num}|{lines[next_seq_num].strip()}".encode('utf-8')
                unreliableSend(packet, server_socket, client_addr, errRate)
                window[next_seq_num] = (packet, time.time())  # Save packet and timestamp
                print(f"Sent packet {next_seq_num}: {lines[next_seq_num].strip()}")
                next_seq_num += 1

            #Wait for ACKs and handle timeouts
            timeout_duration = 0.0001
            server_socket.settimeout(timeout_duration)

            try:
                ack_data, _ = server_socket.recvfrom(1024)
                ack_seq_num = int(ack_data.decode('utf-8').split("|")[1])
                print(f"Received ACK for packet {ack_seq_num}")
                acked.add(ack_seq_num)

                #Slide the window
                while base in acked:
                    base += 1

            except socket.timeout:
                #Retransmit timed-out packets
                for seq_num in range(base, next_seq_num):
                    if seq_num not in acked and time.time() - window[seq_num][1] > timeout_duration:

                        print(f"Retransmitting packet {seq_num}")
                        unreliableSend(window[seq_num][0], server_socket, client_addr, errRate)
                        window[seq_num] = (window[seq_num][0], time.time())  # Update timestamp

        # Step 4: Send FIN packet with sequence number
        fin_seq_num = len(lines)  # Last sequence number + 1
        fin_packet = f"3|{fin_seq_num}".encode('utf-8')
        unreliableSend(fin_packet, server_socket, client_addr, errRate)
        print(f"Sent FIN packet with sequence number {fin_seq_num}. Waiting for client's ACK and FIN.")

        # Step 5: Handle Client's ACK and FIN
        while True:
            try:
                client_response, _ = server_socket.recvfrom(1024)
                response_type, response_seq_num = client_response.decode('utf-8').split("|")
                response_seq_num = int(response_seq_num)

                if response_type == "1" and response_seq_num == fin_seq_num + 1:  # Client's ACK for FIN
                    print(f"Received ACK for FIN from client (seq_num={response_seq_num}).")

                elif response_type == "3":  # Client's FIN packet
                    print(f"Received FIN packet from client (seq_num={response_seq_num}).")
                    # Send ACK for client's FIN
                    fin_ack_packet = f"1|{response_seq_num}".encode('utf-8')
                    unreliableSend(fin_ack_packet, server_socket, client_addr, errRate)
                    print("Sent ACK for client's FIN. Connection closed.")
                    break
            except socket.timeout:
                print("Timeout while waiting for client's ACK or FIN. Retrying...")
                unreliableSend(fin_packet, server_socket, client_addr, errRate)

if __name__ == "__main__":
    main()
