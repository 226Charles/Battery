import requests
import json
import matplotlib.pyplot as plt
from scipy import interpolate
import sys
import datetime

volt_12 = [10.50,11.31,11.58,11.75,11.90,12.06,12.20,12.32,12.42,12.50,12.70]
volt_24 = [21.00,22.62,23.16,23.50,23.80,24.12,24.40,24.64,24.84,25.00,25.40]
volt_48 = [42.00,45.24,46.32,47.00,47.60,48.24,48.80,49.28,49.68,50.00,50.80]
volt_80 = [70.00,75.40,77.20,78.33,79.33,80.40,81.33,82.13,82.80,83.33,84.67]


# 请求的URL和请求体
#2023-06-14 00:00:00
timestamp_start = 1686672000
#2023-06-15 00:00:00
timestamp_end = 1686758400
url = "http://118.25.170.80:8080/can-data/query-by-necessary"
payload = {
    "carrierIdList": [
        "carrier_1684055094a2d2e577-2b63-41c0-afad-3bf5430df5de"
    ],
    "timestamp": "[{},{}]".format(timestamp_start, timestamp_end),
    "fields": ["batteryState", "timestamp", "batteryVolt", "rfid"],
    "firstElseAll": False,
    "timestampAsc": True
}

# 将请求体转换为JSON格式
headers = {
    "Content-Type": "application/json"
    }
data = json.dumps(payload)

# 发送POST请求
response = requests.post(url, data=data, headers=headers)

# 检查响应状态码
if response.status_code == 200:
    print("200 ok")
    # 解析响应内容
    response_data = response.json()
    #print(response_data)
else:
    print(f"请求失败，状态码：{response.status_code}")
    sys.exit()

# 定义一个插值函数
def estimate_battery_percentage(voltage, voltage_curve):
    for i in range(len(voltage_curve)):
        if voltage_curve[i] <= voltage <= voltage_curve[i + 1]:
            voltage_range = voltage_curve[i:i + 2]
            percentage_range = [i * 10, (i + 1) * 10]
            estimated_percentage = (
                (voltage - voltage_range[0]) / (voltage_range[1] - voltage_range[0])
            ) * (percentage_range[1] - percentage_range[0]) + percentage_range[0]
            return estimated_percentage

#print(response_data)

data = response_data['data']
# 将data写入JSON文件
'''with open("t.txt", 'w') as json_file:
    json.dump(response_data, json_file, indent=4)'''
#print(data)
data.sort(key=lambda x: x['timestamp'])
# 提取batteryVolt值和对应的timestamp
battery_volt_values = [entry['batteryVolt'] for entry in data]
timestamps = [entry['timestamp'] for entry in data]

size = len(data)
total_battery_volt = sum(battery_volt_values)
average_battery_volt = total_battery_volt / 1000.0 / size

if 0 <= average_battery_volt <= 16:
    battery_type = "12V"
elif 16 < average_battery_volt <= 30:
    battery_type = "24V"
elif 30 < average_battery_volt <= 56:
    battery_type = "48V"
elif 56 < average_battery_volt <= 100:
    battery_type = "80V"
else:
    battery_type = "未知"

print(battery_type)

battery_voltage_dict = {
    "12V": volt_12,
    "24V": volt_24,
    "48V": volt_48,
    "80V": volt_80
}

# 初始化一个新的列表来存储筛选后的数据
filtered_data = []
# 遍历data并筛选数据
for i in range(len(data)):
    # 跳过第一个数据，因为无法与前一个数据比较
    if i == 0:
        filtered_data.append(data[0])
        continue

    # 计算当前数据与前一个数据的batteryVolt差值
    diff = data[i]['batteryVolt'] - data[i-1]['batteryVolt']

    # 如果差值不超过20，将当前数据添加到筛选后的列表中
    if abs(diff) <= 5:
        filtered_data.append(data[i])

# 定义差值阈值（根据需要调整）
threshold = 20

# 初始化筛选后的数据列表
final_filtered_data = []

# 遍历筛选后的数据，跳过第一个和最后一个数据
for i in range(1, len(filtered_data) - 1):
    # 计算当前数据与前一个数据的batteryVolt差值
    prev_diff = filtered_data[i]['batteryVolt'] - filtered_data[i-1]['batteryVolt']

    # 计算当前数据与后一个数据的batteryVolt差值
    next_diff = filtered_data[i+1]['batteryVolt'] - filtered_data[i]['batteryVolt']

    # 如果差值不超过阈值，将当前数据添加到筛选后的列表中
    if abs(prev_diff) <= threshold and abs(next_diff) <= threshold:
        final_filtered_data.append(filtered_data[i])

# 添加最后一个数据点
final_filtered_data.append(filtered_data[-1])

f_filtered_data = []


filt_battery_volt_values = [entry['batteryVolt'] for entry in final_filtered_data]
filt_timestamps = [entry['timestamp'] for entry in final_filtered_data]
#filt_timestamps = [datetime.datetime.fromtimestamp(entry['timestamp']).strftime("%H:%M:%S") for entry in final_filtered_data]

battery_percentage_values = [estimate_battery_percentage(v/1000.0, battery_voltage_dict[battery_type]) for v in filt_battery_volt_values]
#print(battery_percentage_values)

plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)  # 创建上半部分的子图
plt.plot(filt_timestamps, filt_battery_volt_values, linestyle='-', color='b')
plt.title('Voltage (Moving Average) Over Time')
plt.xlabel('Timestamp')
plt.ylabel('Voltage (V)')
plt.grid(True)

# 创建第二张平滑后的电压曲线图（使用曲线样式）
plt.subplot(2, 1, 2)  # 创建下半部分的子图
plt.plot(filt_timestamps, battery_percentage_values, linestyle='-', color='r')
plt.title('Battery  Over Time')
plt.xlabel('Timestamp')
plt.ylabel('Voltage (V)')
plt.grid(True)

# 调整子图之间的间距
plt.tight_layout()

# 显示图形
plt.show()

# 要估算的电压值
'''target_voltage = 11.99  # 例如，要估算12V电池的电量百分比

# 使用插值函数进行估算
estimated_percentage_12V = estimate_battery_percentage(target_voltage, volt_12)
print(f"估算的电量百分比（12V电池）：{estimated_percentage_12V}%")'''