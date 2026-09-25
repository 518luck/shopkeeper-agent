-- 元数据表结构：存的不是业务数据，而是"数仓自己长什么样"的描述信息
-- 表内容由后续章节的同步脚本写入（读取 conf 下的 yaml 配置 + 反查数仓真实结构）
-- 必须声明客户端编码：容器初始化时的 mysql 客户端默认按 latin1 解释文件字节，
-- 少了这行，下面 COMMENT 里的中文会被存成乱码
SET NAMES utf8mb4;
USE meta;

CREATE TABLE table_info (
  id          VARCHAR(64)  NOT NULL COMMENT '表 ID，与表名一致',
  name        VARCHAR(64)  NOT NULL COMMENT '表名',
  role        VARCHAR(16)           COMMENT '表角色，fact 事实表 / dim 维度表',
  description VARCHAR(512)          COMMENT '表说明',
  PRIMARY KEY (id)
) ENGINE = InnoDB COMMENT = '表信息表';

CREATE TABLE column_info (
  id          VARCHAR(128) NOT NULL COMMENT '字段 ID，格式为 表名.字段名',
  name        VARCHAR(64)  NOT NULL COMMENT '字段名',
  type        VARCHAR(32)           COMMENT '字段数据类型，由同步脚本反查数仓补齐',
  role        VARCHAR(32)           COMMENT '字段角色，primary_key / foreign_key / dimension / measure',
  examples    JSON                  COMMENT '字段示例值',
  description VARCHAR(512)          COMMENT '字段说明',
  alias       JSON                  COMMENT '字段别名',
  table_id    VARCHAR(64)           COMMENT '所属表 ID',
  PRIMARY KEY (id),
  KEY idx_table_id (table_id)
) ENGINE = InnoDB COMMENT = '字段信息表';

CREATE TABLE metric_info (
  id               VARCHAR(64) NOT NULL COMMENT '指标 ID，与指标名一致',
  name             VARCHAR(64) NOT NULL COMMENT '指标名',
  description      VARCHAR(512)         COMMENT '指标说明',
  relevant_columns JSON                 COMMENT '指标相关字段',
  alias            JSON                 COMMENT '指标别名',
  PRIMARY KEY (id)
) ENGINE = InnoDB COMMENT = '指标信息表';

CREATE TABLE column_metric (
  column_id VARCHAR(128) NOT NULL COMMENT '字段 ID',
  metric_id VARCHAR(64)  NOT NULL COMMENT '指标 ID',
  PRIMARY KEY (column_id, metric_id)
) ENGINE = InnoDB COMMENT = '字段与指标关联表';
