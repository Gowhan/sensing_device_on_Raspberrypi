import socket
import time
import pickle
import fcntl

"""
本程序功能：
	定时从data.txt中读取并删除数据
	连接到PC（服务器端）发送数据
"""

print("the client is on.")

# --------------------------------------------------------------------------
# 套接字接口，使用IPv4 & TCP
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定IP和端口，形成套接字
host = input("the IP address of the server: ")  # 服务器IP
port = input("the port of the socket: ")  # 自定义端口号
port = int(port)  # 转换为整型变量

# --------------------------------------------------------------------------
# 连接服务器端
try:
    print("connecting...")
    # 连接服务器
    mySocket.connect((host, port))
    # mySocket.connect(("192.168.137.1", 9999))
    print("connecting successfully.")
except:
    print("connection failure.")

# --------------------------------------------------------------------------
# 定时发送数据
try:
	while True:
		# 读取5行数据
		with open('data.txt', 'r') as f:
			fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 上锁
			data = []
			for i in range(0, 5):
				data.append(f.readline())	            
			fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 解锁
		
		# 删除已处理的5行数据
		with open('data.txt', 'r+') as f:
			fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 上锁
			data = f.readlines()  # 将文件所有内容读取为列表
			f.seek(0)  # 将指针移动到文件开头
			f.write(''.join(data[5:]))  # 写入剩余部分
			f.truncate()  # 截断删除多余部分
			fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 解锁
		
		if data:
			# 处理数据，将数据行按照空格分割然后进行组装
			temperature = []
			humidity = []
			time_collect = ""
			print("5 pieces of data:")
			for i in range(0, 5):
				processed_data = data[i].split()
				# 采样时间记作5条数据中第1条数据的采样时间
				if i == 0:
					time_collect = processed_data[2] + ' ' + processed_data[3]
					
				if (processed_data[0] != "error" and processed_data[1] != "error"):
					temperature.append(float(processed_data[0]))
					humidity.append(float(processed_data[1]))

				print(processed_data[0], processed_data[1], processed_data[2] + ' ' + processed_data[3])
			
			# 对5条数据进行汇总
			# 如果5条全是error，则进入下一次循环
			if temperature == []:
				continue
			# 否则，计算五次采集的平均值，作为准备发送给服务器的一条数据
			print("average:")
			print(sum(temperature) / len(temperature), sum(humidity) / len(humidity), time_collect)
			print("--------------")

			# 将数据装入一个list然后进行发送
			msg = [sum(temperature) / len(temperature), sum(humidity) / len(humidity), time_collect]
			print(msg)
			msg_processed = pickle.dumps(msg)
			mySocket.send(msg_processed)
			print("send successfully.")
			time.sleep(10)

except KeyboardInterrupt:
    print("over.")
    
finally:
    mySocket.close()
    exit()
