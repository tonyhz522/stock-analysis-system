cd stock-analysis-system
# 启动服务
docker compose up -d

# 停止服务
docker compose stop

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 删除服务（保留数据）
docker compose down

# 完全清理（包括数据）
docker compose down -v
rm -rf mysql_data

# run the shell command and start the project
./setup-new.sh
