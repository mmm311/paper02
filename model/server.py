class Server:
    # 默认服务器的cu为64
    cus = 64

    def __init__(self):
        # 已经使用cu的个数，初始值为0
        self.cu_used = 0

        # 未使用cu的个数，初始值为64
        self.cu_unused = Server.cus

    def get_cu_used(self):
        return self.cu_used

    def get_cu_unused(self):
        return self.cu_unused

    def update_cu(self, cu_used):
        self.cu_used = cu_used
        self.cu_unused = Server.cus - self.cu_used



