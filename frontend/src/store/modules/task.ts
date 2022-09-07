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
      return transformDataKey({
        job_id: 3606,
        created_by: 'admin',
        job_type: 'MAIN_INSTALL_PLUGIN',
        job_type_display: '\u5b89\u88c5\u63d2\u4ef6',
        ip_filter_list: [
          '10.0.1.59',
        ],
        total: 0,
        list: [
          {
            filter_host: true,
            bk_host_id: 5,
            ip: '10.0.1.59',
            inner_ip: '10.0.1.59',
            inner_ipv6: null,
            bk_cloud_id: 0,
            bk_cloud_name: '\u76f4\u8fde\u533a\u57df',
            bk_biz_id: 2,
            bk_biz_name: '\u84dd\u9cb8',
            job_id: null,
            status: 'ignored',
            suppressed_by_id: 1597,
            status_display: '\u5f53\u524d\u4e00\u6b21\u6027\u8ba2\u9605\uff08\u4e3b\u673a \u7ea7\uff09\u5df2\u88ab\u4f18\u5148\u7ea7\u66f4\u9ad8\u7684\u7b56\u7565\u3010奇怪的策略(ID: 1597)\u3011\uff08\u4e1a\u52a1 \u7ea7\uff09\u6291\u5236',
            step: '',
          },
        ],
        statistics: {
          total_count: 1,
          failed_count: 0,
          ignored_count: 1,
          pending_count: 0,
          running_count: 0,
          success_count: 0,
        },
        status: 'SUCCESS',
        end_time: '2022-09-06 12:30:23+0800',
        start_time: '2022-09-06 12:30:15+0800',
        cost_time: '8',
        meta: {
          type: 'PLUGIN',
          step_type: 'PLUGIN',
          op_type: 'INSTALL',
          op_type_display: '\u5b89\u88c5',
          step_type_display: '\u63d2\u4ef6',
          name: '',
          category: 'once',
          plugin_name: 'bk-collector',
        },
      });
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
    const data = await getJobCommands(jobId, params).catch(() => {});
    return transformDataKey(data);
  }
}
