# 使用官方 Python 镜像作为基础
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目源代码
COPY . .

# 暴露服务端口
EXPOSE 5000

# 设置启动命令
CMD ["python", "serve.py"]