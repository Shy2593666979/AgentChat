## 一、安装minio

例如现在D盘中创建 D:\minio

在minio文件夹下打开power shell执行以下命令：

```
Invoke-WebRequest -Uri "https://dl.min.io/aistor/minio/release/windows-amd64/minio.exe" -OutFile "minio.exe"

minio.exe --version
```

- 等待minio.exe下载完成

25年之前的minio版本都是带有WebUI的可视化界面，但是最新的版本中WebUI可使用的功能非常少，所以我们先去申请一个人版本的License（单机部署免费的）

申请链接：https://www.min.io/download/aistor-server?platform=windows

<img width="1280" height="607" alt="image" src="https://github.com/user-attachments/assets/dd16ed10-3a76-458d-afb0-1a8b73c08908" />


然后去邮件里面等收到License，下载本地的License之后放到D:\minio中
<img width="898" height="471" alt="image" src="https://github.com/user-attachments/assets/c0f20c39-d857-42e3-ad51-7232e7d959ee" />

因为启动minio需要指定一个存储文件夹，所以还需要在D:\minio下创建一个D:\minio\data文件夹

启动命令是:
```
minio.exe server D:\minio\data --license D:\minio\minio.license
```

这是启动成功后的图片:
<img width="1280" height="410" alt="image" src="https://github.com/user-attachments/assets/e9b442b4-fee4-42cb-9418-dc6f5434ec54" />

然后默认的用户名和用户密码也是对应的access_key_id 和 access_key_scerct

如果需要修改的话，可以执行:

```
setx MINIO_ROOT_USER=admin

setx MINIO_ROOT_PASSWORD=admin123
```

修改完成之后也需要在agentchat中的config.yaml中需要修改对应的access 值

## 二、修改Bucket权限

### 新版本（2025.6后）
现在算是将MiniO正常的部署到本机了，下面只需一步就大功告成，就是将agentchat的bucket权限全部放出来

打开浏览器（需要保证minio 服务是启动中）
```
http://127.0.0.1:9001/console/buckets/agentchat/admin/prefix
```

新版本访问这个网页创建访问权限
<img width="1280" height="575" alt="image" src="https://github.com/user-attachments/assets/e623dc86-d4b2-4d03-881e-8e7d852fabba" />

`/代表的是当前bucket下的全部文件`

readwrite相当于是开放读写权限

### 老版本

老版本创建访问权限（docker部署的是老版本的minio）
<img width="1920" height="910" alt="170e76f735c75ea9a90807f7d60703f1" src="https://github.com/user-attachments/assets/4ec320f9-6cb6-465b-854c-456633a57b91" />


## 总结
这就是整体的一个Windows下部署minio的过程了，如果使用docker 进行启动服务的话，不需要担心license的问题，因为使用的是老版本，不需要license即可使用更多的功能
