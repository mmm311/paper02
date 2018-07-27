import math
from config import constant
from model import VM
from model import Host

class FATOS:
    def __init__(self, threshold):
        # R-CE 失败容忍度
        self.threshold = threshold
        self.hosts = []
        # 时间片
        self.split_time = 30 * 60
        # 取消时间
        self.cancel_time = 15 * 60
        # hosts的字典，key host的id, valuehost对象
        self.hosts_dict = None

        self.vm_instances = []


    def FATOS(self, wfs):
        time = 0
        for wf in wfs:
           for task in  wf.task_list:
                resource_replicate = self.replication_delay(task, self.vm_instances)
                resoruce_checkpoint = self.checkpoint_delay(task, self.vm_instances)
                if resource_replicate == math.inf and resoruce_checkpoint == math.inf:
                    # 拒绝服务
                    pass
                else:
                    # 考虑复制
                    resource_option = min(resource_replicate, resoruce_checkpoint)
                    # 找出最优的虚拟机
                    # 找不到就开启新的虚拟机
        if time == 30 * 60:
            self.scale_down_vm()


    def scale_down_vm(self, vm_list):
        for vm in vm_list:
            if len(vm.excutor_time[-1]) == 1:
                start_time, end_time = vm.excutor_time[-1]
                idle_time = self.split_time - end_time
                if idle_time < self.cancel_time:
                    vm.excutor_time.append([self.split_time, self.split_time])
                else:
                    host_id = vm.host_id
                    host = self.hosts_dict.get(host_id)
                    # 计算当前vm 使用情况 没有写
                    host.cu_remain = host.cu_remain + vm.cu
                    host.cu_used = host.cu_used - vm.cu

                    if host.cancel_server():
                        for host_vm in host.vms:
                            for other_host in self.hosts:
                                if not other_host.cancel_server():
                                    if other_host.cu_remain >= host_vm.cu:
                                        other_host.cu_remain = other_host.cu_remain - host_vm.cu
                                        other_host.cu_used = other_host.cu_used + host_vm
                                        host.cu_remain = host.cu_remain + host_vm.cu
                                        host.cu_used = host.cu_used - host_vm.cu

                    if host.cu_remain == host.cus:
                        self.hosts.remove(host)

    def scale_vm(self, cu):
        self.hosts.sort(key=lambda host: host.cu_remain, reverse=False)
        for host in self.hosts:
            if host.cu_remain >= cu:
                host.cu_used = host.cu_used + cu
                host.cu_remain = host.cu_remain - cu
                return True
        host = Host()
        if host.cu_remain >= cu:
            host.cu_used = host.cu_used + cu
            host.cu_remain = host.cu_remain - cu
            self.hosts.append(host)
            return True
        else:
            return False


    '''
    实现延迟备份,遍历候选虚拟机找出最佳虚拟机和资源。
    当service_time <allocate_time 时延迟备份主要有两种场景
    场景1：service_time < allocate_time <= 2 * service_time 时，backup部分和
    primary 执行 
    场景2： service_time * 2 < allocate_time 时，backup 等primary执行完成再执行

    @:param task 任务
    @:param vms 候选虚拟机
    @:return 最优虚拟机 和最优资源需求
    '''
    def replication_delay(self, task, vms):
        optimize_vm = math.inf
        optimize_resource = math.inf
        resource = math.inf
        allocate_time = task.allocate_time
        for vm in vms:
            service_time = task.work_load / vm.cu
            task.service_time = task.receive_time + service_time + task.transmit_time
            if allocate_time > service_time:
                if service_time <= allocate_time < 2 * service_time:
                    resource = self.replication_case1(task, vm)
                elif allocate_time > 2 * service_time:
                    resource = self.replication_case2(task, vm)

            if resource < optimize_resource:
                optimize_resource = resource
                optimize_vm = vm.instance

        return optimize_vm, optimize_resource

    '''
    实现了checkpoint_delay算法，checkpoint_delay算法有两种场景:
    1. service_time < allocate_time < 2 * service_time 
    2. allocate_time >= 2 * service_time 
    @:param task 任务
    @:param vms 候选虚拟机集合
    @:return 最优虚拟机和最优资源
    '''
    def checkpoint_delay(self, task, vms):
        optimize_vm = math.inf
        optimize_resource = math.inf
        resource = math.inf
        allocate_time = task.allocate_time
        for vm in vms:
            chunk, service_time = self.find_best_chunk(task, vm)
            task.service_time = service_time

            if allocate_time > service_time:
                if service_time <= allocate_time < 2 * service_time:
                    resource = self.checkpoint_case1(task, vm)
                if allocate_time >= 2 * service_time:
                    resource = self.checkpoint_case2(task, vm)
            if optimize_resource > resource:
                optimize_resource = resource
                optimize_vm = vm

        return optimize_vm, optimize_resource

    '''
    checkpoint的第一个场景
    @:param task 任务
    @:param vm 候选虚拟机
    @:return 资源
    '''
    def checkpoint_case1(self, task, vm):
        service_time = task.service_time
        cu = vm.cu
        probility01 = FATOS.reliability_host(service_time)
        resource01 = service_time * cu + (2 * service_time - task.allocate_time) * cu
        probility02 = 1 - probility01
        resource02 = 2 * service_time * cu
        resource = probility01 * resource01 + probility02 * resource02
        return resource

    '''
      checkpoint的第二个场景
      @:param task 任务
      @:param vm 候选虚拟机
      @:return 资源
    '''
    def checkpoint_case2(self, task, vm):
        service_time = task.service_time
        cu = vm.cu
        probility01 = FATOS.reliability_host(service_time)
        resource01 = service_time * cu
        probility02 = 1 - probility01
        resoruce02 = 2 * service_time * cu
        resource = probility01 * resource01 + probility02 * resoruce02
        return resource

    '''
    服务器在计算任务时，计算该服务器的可靠性
    @:param service_time 任务的服务时间
    @:return 服务器的可靠性
    '''
    @staticmethod
    def reliability_host(service_time):
        return math.exp(service_time * constant.HOST_FAULT)

    '''
    采用不同的任务块数计算每个任务块数的服务时间
    服务时间呈现先下降再上升
    找出给定虚拟机最佳的分块大小和服务时间
    @:param task 任务
    @:param vm 候选虚拟机
    @:return 最优的任务的块数和最优的执行时间
    '''
    def find_best_chunk(self, task, vm):
        optimize_chunk = math.inf
        optimize_service_time = math.inf
        previous_chunk = math.inf
        previous_service_time = math.inf
        chunk = 1
        iterator = 1
        while True and iterator < constant.MAX_CHUNK:
            service_time = self.service_time_for_chunk(task, vm, chunk)
            if previous_chunk == math.inf:
                previous_service_time = service_time
                previous_chunk = chunk
            else:
                # 如果前一个服务时间小于当前服务时间，那么前一个服务时间最优
                # 它对应chunk 就是最优。否则更新previous_service_time和
                # previous_chunk
                if previous_service_time < service_time:
                    optimize_service_time = previous_service_time
                    optimize_chunk = previous_chunk
                    break
                else:
                    previous_chunk = chunk
                    previous_service_time = service_time

            chunk = chunk + 1
            iterator = iterator + 1

        return optimize_chunk, optimize_service_time

    '''
    根据任务的块数计算任务的服务时间
    @:param task 任务
    @:param vm 候选虚拟机
    @:param chunk 任务被划分的块数
    @:return 任务服务时间
    '''
    def service_time_for_chunk(self, task, vm, chunk):
        service_time = task.work_load / vm.cu
        service_time = task.receive_time + service_time + task.transmit_time
        return (chunk * (1 / constant.VM_FAULT + constant.RECOVERY) *
                (math.exp(constant.VM_FAULT * (service_time / chunk + constant.CHECKPOINT)) - 1))


    '''
    实现延迟备份第一种场景，延迟备份第一种场景有两种情况
    第一种：primary 执行成功 注意：backup部分执行
    第二种：primary 执行不成功, backup 继续执行
    @:param task 任务
    @:param vm 虚拟机
    @:return 对于 vm(k)实现延迟备份第一种场景的需要的资源
    '''
    def replication_case1(self, task, vm):
        cu = vm.cu
        service_time = task.service_time
        replication_num = self.replication_num(service_time)
        num_primary = replication_num / 2
        num_backup = replication_num - num_primary
        probality01 = 1 - math.pow((1 - FATOS.reliability_vm(service_time)), num_primary)
        resource01 = num_primary * service_time * cu
        + num_backup * (2 * service_time - task.allocate_time) * cu
        probality02 = math.pow(1 - FATOS.reliability_vm(service_time), num_primary)
        resource02 = replication_num * service_time * cu
        resource = probality01 * resource01 + probality02 * resource02
        return resource

    '''
    实现延迟备份第二种场景，延迟备份第二种场景有两种情况
    第一种：primary 执行成功 注意：backup 还没开始执行
    第二种：primary 执行不成功, backup 继续执行
    @:param task 任务
    @:param vm 虚拟机
    @:return 对于 vm(k)实现延迟备份第二种场景的需要的资源
    '''

    def replication_case2(self, task, vm):
        cu = vm.cu
        service_time = task.service_time
        replication_num = self.replication_num(service_time)
        num_primary = replication_num / 2
        probality01 = 1 - math.pow(1 - FATOS.reliability_vm(service_time), num_primary)
        resource01 = num_primary * service_time * cu
        probality02 = math.pow(1 - FATOS.replication_num(service_time), num_primary)
        resource02 = replication_num * service_time * cu
        resource = probality01 * resource01 + probality02  * resource02
        return resource

    '''
    虚拟机在计算任务时，计算该虚拟机的可靠性
    @:param service_time 任务的服务时间
    @:return 虚拟机的可靠性
    '''
    @staticmethod
    def reliability_vm(service_time):
        return math.exp(service_time * constant.VM_FAULT)

    '''
    根据虚拟机的靠性计算虚拟机需要备份的数量
    @:param 任务的服务的时间
    @:return 备份虚拟机的个数
    '''
    def replication_num(self, service_time):
        return math.log(self.threshold, 1 - FATOS.reliability_vm(service_time)) + 1
