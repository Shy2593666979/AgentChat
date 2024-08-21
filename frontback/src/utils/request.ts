// axios的封装处理
import axios from 'axios'
// 1.根域名配置
// 2.超时时间
// 3.请求拦截器,响应拦截器

const request = axios.create({
    baseURL:'http://geek.itheima.net/v1_0',
    timeout: 5000
})

// 添加请求拦截器
// 在请求发送之前 做拦截 插入一些自定义配置 【参数的处理】
request.interceptors.request.use(function (config) {
    // 在发送请求之前做些什么  操作config注入我们的token数据
    // 1.获取token
    // 2.按照后端的格式做token的拼接
    return config;
  }, function (error) {
    // 对请求错误做些什么
    return Promise.reject(error);
  });

// 添加响应拦截器
// 在响应返回到客户端之前 做拦截 重点处理返回的数据
request.interceptors.response.use(function (response) {
    // 2xx 范围内的状态码都会触发该函数。
    // 对响应数据做点什么
    return response;
  }, function (error) {
    // 超出 2xx 范围的状态码都会触发该函数。
    // 对响应错误做点什么
    console.dir(error)
    if (error.response.status === 401){
      window.location.reload()
    }
    return Promise.reject(error);
  });

export { request }