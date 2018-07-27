class Host:
    # 默认服务器的cu为64
    cus = 64

    # 主机最低利用率
    low_rate = 0.25

    def __init__(self):
        # 已经使用cu的个数，初始值为0
        self.cu_used = 0

        # 未使用cu的个数，初始值为64
        self.cu_remain = Host.cus

        # host上面的虚拟机
        self.vms = []

    '''
    @:param
    获取已经使用的cu的数量
    '''
    def get_cu_used(self):
        return self.cu_used

    '''
    @:param
    获取尚未使用的cu的数量
    '''
    def get_cu_remain(self):
        return self.cu_remain

    '''
    @:param cu_used 已经使用cu的数量
    更新cu的已经使用数量和未使用的数量
    '''
    def update_cu(self, cu_used):
        self.cu_used = cu_used
        self.cu_remain = Host.cus - self.cu_used

    '''
    @:param
    如果物理服务器的利用率低于阈值，则该服务器可能会被注销
    '''
    def cancel_server(self):
        if self.cu_used <= Host.cus * Host.low_rate:
            return True
        else:
            return False



