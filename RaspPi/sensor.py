import RPi.GPIO as GPIO
import time

class DHT11_(object):
    def __init__(self, pin_D):
        self._pin = pin_D   # 成员为：data引脚编号

    def read_data(self):
        """
        读取传感器数据
        :return:
        """
        # 数据采集，开发板输出至 DHT --------------------------------------------------------------
        # 激活输出引脚
        GPIO.setup(self._pin, GPIO.OUT)
        # 输出高电平，持时0.05s，使 DHT 进入空闲状态
        GPIO.output(self._pin, GPIO.HIGH)
        time.sleep(0.05)
        # 输出低电平，持时0.02s（大于0.018s即可），使 DTH 开始数据采集
        GPIO.output(self._pin, GPIO.LOW)
        time.sleep(0.02)

        # 数据传输，DHT 输出至开发板 ---------------------------------------------------------------
        # 激活输入引脚，上拉电平
        GPIO.setup(self._pin, GPIO.IN, GPIO.PUD_UP)
        # 接收数据
        data = self.collect_data()

        # 数据处理 --------------------------------------------------------------------------------
        # 统计高电平段数，若不为40，则中断并返回
        data_high_state = self.count_high_state(data)
        if len(data_high_state) != 40:
            return False, 0
        # 将电平转换为比特串（转换规则见函数）
        data_bits = self.high_state_to_bits(data_high_state)
        # 将比特串转化为字节串（字节串用于校验）
        data_bytes = self.bits_to_bytes(data_bits)

        # 数据校验 ---------------------------------------------------------------------------------
        # 根据前三个字节计算校验位
        data_check = self.check(data_bytes)
        # 若校验失败，则中断并返回
        if data_bytes[4] != data_check:
            return False, 0

        # 解读数据 ---------------------------------------------------------------------------------
        # 四个字节依次为：湿度的整数部分，湿度的小数部分，温度的整数部分，温度的小数部分
        humidity = data_bytes[0] + float(data_bytes[1]) / 10
        temperature = data_bytes[2] + float(data_bytes[3]) / 10

        return True, [humidity, temperature]


    def collect_data(self):
        """
        实现数据收集，高电平为1，低电平为0
        电平长时间不变之后返回
        :return:list，当中连续0/1出现的次数代表对应电平的持时
        """
        lasting_epoch = 0    # 记录当前电平持续的轮次（反应持时）
        lasting_epoch_max = 100    # 当前电平持续轮次的上限
        last_state = -1     # 记录上一轮循环中的电平高低
        data = []       # 记录数据，高电平记录为1，低电平记录为0
        while True:
            # 采集当前电平
            current_state = GPIO.input(self._pin)
            data.append(current_state)

            # 如果这一轮循环采集到的电平不等于上一轮电平，则轮次清零，为下一轮循环更新上一轮的电平
            # 如果电平相等，轮次累加，当轮次超过阈值时，表示采集完毕并跳出循环
            if last_state != current_state:
                lasting_epoch = 0
                last_state = current_state
            else:
                lasting_epoch += 1
                if lasting_epoch > lasting_epoch_max:
                    break
        return data

    def count_high_state(self, data):
        """
        统计波形中高电平的段数，也即实际有效数据中的bit数
        :param data: list，包含一串0和1，其中连续的0/1个数表示实际高低电平的持续时间
        :return: list，包含一串整数，每一个整数代表对应高电平的持时
        """
        # 数据传输期间的五个状态：1.初始延时，2.起始低电平，3.起始高电平，4.数据低电平，5.数据高电平
        state = 1   # 记录当前状态代号
        data_high_state = []      # 记录每一段电平的持续时间
        current_lasting_time = 0    # 记录当前电平已持续的时间

        for i in range(len(data)):
            current_state = data[i]   # 记录本轮次电平高低
            current_lasting_time += 1   # 持时自增

            # 状态1，current_state应为HIGH，否则进入state 2
            if state == 1:
                if current_state == GPIO.HIGH:
                    continue
                else:
                    state = 2
                    continue
            # 状态2，current_state应为LOW，否则进入state 3
            if state == 2:
                if current_state == GPIO.LOW:
                    continue
                else:
                    state = 3
                    continue
            # 状态3，current_state应为HIGH，否则进入state 4
            if state == 3:
                if current_state == GPIO.HIGH:
                    continue
                else:
                    state = 4
                    continue
            # 状态4，current_state应为LOW，否则进入state 5并且电平计数清零
            if state == 4:
                if current_state == GPIO.LOW:
                    continue
                else:
                    state = 5
                    current_lasting_time = 0
                    continue
            # 状态5，current_state应为HIGH，否则进入state 4并且将当前电平计数进行保存
            if state == 5:
                if current_state == GPIO.HIGH:
                    continue
                else:
                    data_high_state.append(current_lasting_time)  # 这一波高电平的持时结束，记录下来
                    state = 4
                    continue
        return data_high_state

    def high_state_to_bits(self, data_high_state):
        """
        将一段长短不一的高电平转换为0/1比特串
        转换规则：持时长的高电平为1，持时短的高电平为0
        :param data_high_state: list，包含一串整数，每一个整数代表对应高电平的持时
        :return: list，包含一串布尔值，True表示长持时的高电平（即1），False表示短持时的高电平（即0）
        """
        longest_lasting_time = 0    # 记录最长的持时
        shortest_lasting_time = 100    # 记录最短的持时

        for i in range(len(data_high_state)):
            if data_high_state[i] < shortest_lasting_time:
                shortest_lasting_time = data_high_state[i]
            if data_high_state[i] > longest_lasting_time:
                longest_lasting_time = data_high_state[i]

        # 取 最大持时和最小持时的均值 为分割点
        threshold = (longest_lasting_time + shortest_lasting_time) / 2
        data_bits = []

        # 解码
        for i in range(0, len(data_high_state)):
            if data_high_state[i] > threshold:
                data_bits.append(True)
            else:
                data_bits.append(False)

        return data_bits

    def bits_to_bytes(self, data_bits):
        """
        将比特串转换为字节串
        :param data_bits:
        :return:
        """
        data_bytes=[]
        current_byte = 0

        for i in range(len(data_bits)):
            current_byte = current_byte << 1
            if data_bits[i] == True:
                current_byte = current_byte | 1
            else:
                current_byte = current_byte | 0

            # 处理了8个bit后进行一次清零，并将对应字节结果进行保存
            if ((i + 1) % 8 == 0):
                data_bytes.append(current_byte)
                current_byte = 0

        return data_bytes

    def check(self, data_bytes):
        """
        计算校验
        :return:
        """
        return (data_bytes[0] + data_bytes[1] + data_bytes[2] + data_bytes[3]) & 255

# if __name__ == "__main__":
    # dht11_pin = 18  # 补全引脚名称
    # GPIO.setmode(GPIO.BCM)
    # DHT11 = DHT11_(dht11_pin)

    # try:
        # while True:
            # flag, result = DHT11.read_data()
            # if flag == True:
                # print("temperature: %-3.1f"% result[1])
                # print("humidity: %-3.1f"% result[0])
            # else:
                # print("ERROR")
            # time.sleep(2)
    # except KeyboardInterrupt:
        # print("\n Ctrl + C QUIT")
    # finally:
        # GPIO.cleanup()
