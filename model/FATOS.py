import math
from config.constant import *

class FATOS:
    def __init__(self, threshold):
        # R-CE 失败容忍度
        self.threshold = threshold
        pass


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
        optimize_vm = -1
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
        return math.exp(service_time * RELIABILITY)

    '''
    根据虚拟机的靠性计算虚拟机需要备份的数量
    @:param 任务的服务的时间
    @:return 备份虚拟机的个数
    '''
    def replication_num(self, service_time):
        return math.log(self.threshold, 1 - FATOS.reliability_vm(service_time)) + 1

