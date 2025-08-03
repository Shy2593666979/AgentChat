// axios的封装处理
import axios from 'axios'
// 1.根域名配置
// 2.超时时间
// 3.请求拦截器,响应拦截器

const request = axios.create({
    baseURL:'',
    timeout: 10000  // 全局超时10秒，对于耗时操作单独设置
})

// 添加请求拦截器
request.interceptors.request.use(function (config) {
  // 添加token到请求头
  const token = localStorage.getItem('token');
  if (token) {
    // 确保headers对象存在
    config.headers = config.headers || {};
    config.headers['Authorization'] = `Bearer ${token}`;
    
    // 调试用
    // console.log('已添加Authorization头:', `Bearer ${token.substring(0, 10)}...`)
  }
  
  // 删除可能泄露敏感信息的日志
  // console.log('发送请求:', config.method?.toUpperCase(), config.url)
  // console.log('请求数据:', config.data)
  // console.log('请求头:', config.headers)
  
  return config;
}, function (error) {
  // 对请求错误做些什么
  console.error('请求拦截器错误:', error)
  return Promise.reject(error);
});

// 添加响应拦截器
request.interceptors.response.use(function (response) {
  // 2xx 范围内的状态码都会触发该函数。
  // 对响应数据做点什么
  // 删除可能泄露敏感信息的日志
  // console.log('收到响应:', response.status, response.config.url)
  // console.log('响应数据:', response.data)
  return response;
}, function (error) {
  // 超出 2xx 范围的状态码都会触发该函数。
  // 对响应错误做点什么
  console.error('响应错误:', error.response?.status, error.config?.url)
  console.error('错误详情:', error.response?.data || error.message)
  
  if (error.response?.status === 401) {
    // token过期，清除本地存储并跳转到登录页
    localStorage.removeItem('token');
    localStorage.removeItem('userInfo');
    window.location.href = '/login';
  }
  return Promise.reject(error);
});

export { request }
