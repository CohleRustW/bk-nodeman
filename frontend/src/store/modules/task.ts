import { VuexModule, Module, Action, Mutation } from 'vuex-module-decorators';
import {
  listJob, // 任务列表
  retrieveJob, // 任务详情 & 主机列表
  getJobLog, // 查询日志
  retryJob, // 重试
  retryNode, // 原子重试
  revokeJob, // 终止
  collectJobLog, // 日志上报
  getJobCommands, // 获取手动安装命令
} from '@/api/modules/job';
import { getFilterCondition } from '@/api/modules/meta';
import { transformDataKey, sort } from '@/common/util';
import { ITaskParams, IHistory, ITask, ITaskHost } from '@/types/task/task';
import { ISearchChild, ISearchItem } from '@/types';

interface IJob {
  jobId: number
  params: ITaskParams,
  canceled?: boolean
}

// eslint-disable-next-line new-cap
@Module({ name: 'task', namespaced: true }) // 命名冲突、调用两次
export default class TaskStore extends VuexModule {
  public routetParent = '';

  @Mutation
  public setRouterParent(name: string) {
    this.routetParent = name;
  }
  // 历史任务列表
  @Action
  public async requestHistoryTaskList(params: ITaskParams) {
    const data = await listJob(params).catch(() => ({
      total: 0,
      list: [],
      filterCondition: [],
    }));
    data.list.forEach((row: ITaskHost) => {
      row.status = row.status.toLowerCase();
    });
    return transformDataKey(data) as { total: number, list: IHistory[] };
  }
  // 单个任务详情, 包含主机列表
  @Action
  public async requestHistoryTaskDetail({ jobId, params, canceled = false }: IJob) {
    const res: ITask = await retrieveJob(jobId, params).catch(() => {});
    if (res) {
      res.list.forEach((row: ITaskHost) => {
        if (row.bk_cloud_id === 0 || row.bk_cloud_name === 'default area') {
          row.bk_cloud_name = window.i18n.t('直连区域');
        }
        row.status = row.status.toLowerCase();
      });
      return transformDataKey(res);
    }
    return canceled ? { canceled: true } : false;
  }
  // 主机日志详情
  @Action
  public async requestHistoryHostLog({ jobId, params }: IJob) {
    const data = await getJobLog(jobId, params).catch(() => {});
    if (data) {
      data.forEach((row: ITaskHost) => {
        row.status = row.status.toLowerCase();
      });
    }
    return data;
  }
  // 任务重试
  @Action
  public async requestTaskRetry({ jobId, params }: IJob) {
    const data = await retryJob(jobId, params, { needRes: true }).catch(() => ({}));
    return data;
  }
  // 任务终止
  @Action
  public async requestTaskStop({ jobId, params }: IJob) {
    const res = await revokeJob(jobId, params, { needRes: true }).catch(() => ({}));
    return res;
  }
  // 原子重试
  @Action
  public async requestNodeRetry({ jobId, params }: IJob) {
    const res = await retryNode(jobId, params, { needRes: true }).catch(() => ({}));
    return res;
  }
  // 获取筛选条件
  @Action
  public async getFilterList(params: Dictionary = { category: 'job' }) {
    const data = await getFilterCondition(params).then((res: ISearchItem[]) => {
      const userName = window.PROJECT_CONFIG ? window.PROJECT_CONFIG.USERNAME || '' : '';
      const list = res.map((item: ISearchItem) => {
        item.multiable = true;
        if (item.id === 'job_type' && Array.isArray(item.children)) {
          const sortAgent: ISearchChild[] = [];
          const sortProxy: ISearchChild[] = [];
          const sortPlugin: ISearchChild[] = [];
          const sortOther: ISearchChild[] = [];
          item.children.forEach((item: ISearchChild) => {
            if (/agent/ig.test(item.id)) {
              sortAgent.push(item);
            } else if (/proxy/ig.test(item.id)) {
              sortProxy.push(item);
            } else if (/plug/ig.test(item.id)) {
              sortPlugin.push(item);
            } else {
              sortOther.push(item);
            }
          });
          item.children = (sort(sortAgent, 'name') || []).concat(
            sort(sortProxy, 'name') || [],
            sort(sortPlugin, 'name') || [],
            sort(sortOther, 'name') || [],
          );
        }
        if (userName && item.id === 'created_by' && item.children && item.children.length) {
          item.children.forEach((item) => {
            if (item.id === userName) {
              item.name = window.i18n.t('我');
            }
          });
        }
        if (item.children && item.children.length) {
          item.children = item.children.map((child) => {
            child.checked = false;
            return child;
          });
        }
        return item;
      });
      return list;
    })
      .catch(() => []);
    return data;
  }
  // 日志上报
  @Action
  public async requestReportLog({ jobId, params }: IJob) {
    const data = await collectJobLog(jobId, params).catch(() => {});
    return data;
  }
  @Action
  public async requestCommands({ jobId, params }: { jobId: number, params: { 'bk_host_id': number } }) {
    const data = await getJobCommands(jobId, params).catch(() => ({
      solutions: [
        {
          name: 'shell',
          description: '通过 Unix-like shell 进行安装',
          steps: [
            {
              type: 'commands',
              contents: [
                {
                  name: 'create_tmp_dir_cmd',
                  text: 'mkdir -p C:/tmp/',
                  description: '创建临时目录',
                  show_description: false,
                },
                {
                  name: 'curl.exe',
                  text: 'curl http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/curl.exe -o C:/tmp/curl.exe --connect-timeout 5 -sSf',
                  description: '数据传输工具, 用于下载文件依赖',
                  show_description: true,
                },
                {
                  name: 'ntrights.exe',
                  text: 'curl http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/ntrights.exe -o C:/tmp/ntrights.exe --connect-timeout 5 -sSf',
                  description: '用户赋权工具',
                  show_description: true,
                },
                {
                  name: 'curl-ca-bundle.crt',
                  text: 'curl http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/curl-ca-bundle.crt -o C:/tmp/curl-ca-bundle.crt --connect-timeout 5 -sSf',
                  description: 'TLS Certificate Verification',
                  show_description: true,
                },
                {
                  name: 'libcurl-x64.dll',
                  text: 'curl http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/libcurl-x64.dll -o C:/tmp/libcurl-x64.dll --connect-timeout 5 -sSf',
                  description: 'libcurl 共享库, 补丁文件',
                  show_description: true,
                },
              ],
              description: '依赖文件下载',
            },
            {
              type: 'commands',
              contents: [
                {
                  name: 'download_cmd',
                  text: 'C:/tmp/curl.exe http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/setup_agent.bat -o C:/tmp/setup_agent.bat --connect-timeout 5 -sSf',
                  description: '下载安装脚本',
                  show_description: false,
                },
                {
                  name: 'chmod_cmd',
                  text: 'chmod +x C:/tmp/setup_agent.bat',
                  description: '为 setup_agent.bat 添加执行权限',
                  show_description: false,
                },
              ],
              description: '下载安装脚本并赋予执行权限',
            },
            {
              type: 'commands',
              contents: [
                {
                  name: 'run_cmd',
                  text: 'nohup C:/tmp/setup_agent.bat -O 48533 -E 59173 -A 58625 -V 58930 -B 10020 -S 60020 -Z 60030 -K 10030 -e "9.135.246.142 " -a "9.134.110.184,9.135.227.167,9.135.246.142 " -k "9.135.246.142 " -l http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download -r http://9.134.239.232:30300/backend -i 0 -I 9.134.81.161 -T C:\\\\tmp\\\\ -p c:\\\\gse -c oEoyezRbGRinCqdD5uobEoHNOHkneTDfB0d1pqNb9uXmpkhLuanNEdbE -s xxx -N SERVER &> C:/tmp/nm.nohup.out &',
                  description: '执行安装脚本',
                  show_description: false,
                },
              ],
              description: '执行安装脚本',
            },
          ],
          target_host_solutions: [],
        },
        {
          name: 'batch',
          description: '通过 Windows 批处理脚本 进行安装',
          steps: [
            {
              type: 'commands',
              contents: [
                {
                  name: 'pre_command',
                  text: 'mkdir C:\\tmp\\',
                  description: '创建临时目录',
                  show_description: false,
                },
              ],
              description: '创建临时目录',
            },
            {
              type: 'dependencies',
              contents: [
                {
                  name: 'curl.exe',
                  text: 'http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/curl.exe',
                  description: '数据传输工具, 用于下载文件依赖',
                  show_description: false,
                },
                {
                  name: 'tcping.exe',
                  text: 'http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/ntrights.exe',
                  description: '用户赋权工具',
                  show_description: false,
                },
                {
                  name: 'curl-ca-bundle.crt',
                  text: 'http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/curl-ca-bundle.crt',
                  description: 'TLS Certificate Verification',
                  show_description: false,
                },
                {
                  name: 'libcurl-x64.dll',
                  text: 'http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/libcurl-x64.dll',
                  description: 'libcurl 共享库, 补丁文件',
                  show_description: false,
                },
              ],
              description: '依赖文件下载',
            },
            {
              type: 'commands',
              contents: [
                {
                  name: 'download_cmd',
                  text: 'C:\\tmp\\curl.exe http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download/setup_agent.bat -o C:\\tmp\\setup_agent.bat -sSf',
                  description: '下载安装脚本',
                  show_description: false,
                },
                {
                  name: 'run_cmd',
                  text: 'C:\\tmp\\setup_agent.bat -O 48533 -E 59173 -A 58625 -V 58930 -B 10020 -S 60020 -Z 60030 -K 10030 -e "9.135.246.142" -a "9.134.110.184,9.135.227.167,9.135.246.142" -k "9.135.246.142" -l http://bkrepo.bk-dev.woa.com/generic/bksaas-addons/public-bkapp-bk_nod-3/data/bkee/public/bknodeman/download -r http://9.134.239.232:30300/backend -i 0 -I 9.134.81.161 -T C:\\tmp\\ -p c:\\gse -c oEoyezRbGRinCqdD5uobEoHNOHkneTDfB0d1pqNb9uXmpkhLua+ZoO4V1wIY -s xxx -N SERVER',
                  description: '执行安装脚本',
                  show_description: false,
                },
              ],
              description: '执行安装命令',
            },
          ],
          target_host_solutions: [],
        },
      ],
    }));
    return transformDataKey(data);
  }
}
