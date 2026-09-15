-- 建库：meta 存元数据（表/字段/指标），dw 模拟业务数仓
CREATE DATABASE IF NOT EXISTS meta
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS dw
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

-- compose 里只声明了 MYSQL_USER，未声明 MYSQL_DATABASE，
-- 因此需要在这里显式授权，否则应用账号连不上这两个库
GRANT ALL PRIVILEGES ON meta.* TO 'didilili'@'%';
GRANT ALL PRIVILEGES ON dw.* TO 'didilili'@'%';
FLUSH PRIVILEGES;
