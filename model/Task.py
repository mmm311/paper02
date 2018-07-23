
class Task:
   """
    :param task_id :任务id
        pre_task_id_list: 前继任务id
        suc_task_id_list: 后继任务id
   """

   def __init__(self, task_id, pre_task_id_list = [], suc_task_id_list = []):
        self.task_id = task_id
        self.pre_task_id_list = pre_task_id_list
        self.suc_task_id_list = suc_task_id_list
        self.work_load = 0
        self.input_data = 0
        self.output_data = 0

        # 执行虚拟机
        self.vm = 0

        self.exc_time = 0
        self.start_time = 0
        self.end_time = 0