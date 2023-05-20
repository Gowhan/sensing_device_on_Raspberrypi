import pymysql
import socket
import time
import pickle

print("The server is on.")

# -----------------------------------------------------------------------------
# 套接字接口，使用IPv4 & TCP
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定IP和端口，形成套接字
hostname = socket.gethostname()  # 本机名
host = socket.gethostbyname(hostname)  # 本机IP
port = 9999  # 自定义端口号
print("the IP address of the server: %s" % host)
print("the port of the socket: %d" % port)
mySocket.bind((host, port))

# 设置TCP连接请求队列的最大数量
mySocket.listen(5)

# -----------------------------------------------------------------------------
# 打开数据库连接
myDataBase = pymysql.connect(
    host="",
    port=3306,
    user="",
    password="",
    database=""
)
print("the database is on.")

# 实例化一个游标对象cursor
cursor = myDataBase.cursor()

# -----------------------------------------------------------------------------
# 连接客户端，接收信息并插入数据库
while True:
    print("connecting...")

    # 接收客户端连接
    client, address = mySocket.accept()
    print("connect successfully.")

    # 显示客户端的套接字信息
    print("IP address of the client: %s" % address[0])
    print("the port of the socket: %d" % address[1])

    while True:
        # 利用客户端的套接字读取消息
        msg_processed = client.recv(1024)  # 开辟缓冲区，大小为1024Bytes
        msg = pickle.loads(msg_processed)
        temperature = float(msg[0])
        humidity = float(msg[1])
        time_collect = msg[2]
        print(temperature, humidity, time_collect)  # 把接收到的数据进行解码，并打印显示一下
        print("message received.")

        # SQL 插入语句
        sql = """INSERT INTO demo (TEMP, HUMI, TIME) VALUES (%s, %s, %s);"""
        values = (temperature, humidity, time_collect)

        try:
            # 执行sql语句
            cursor.execute(sql, values)
            # 提交到数据库执行
            myDataBase.commit()
            print("Insert successfully.")
        except:
            # 如果发生错误则回滚
            myDataBase.rollback()
            print("Insertion Error")
        time.sleep(10)

        # if msg == "over":
        #     client.close()
        #     mySocket.close()
        #     # 关闭数据库连接
        #     myDataBase.close()
        #     print("程序结束\n")
        #     exit()

