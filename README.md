# hostloc自动签到脚本

## 功能
- hostloc自动签到
- 自动刷访问奖励

## 使用

### docker
```shell
docker run -d --rm --name hostloc-checkin -e HOSTLOC_USERNAME=username -e HOSTLOC_PASSWORD=password  furacas/hostloc-checkin:latest
```

