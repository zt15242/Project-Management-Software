# **NEO开发规范**

## 一、包名规范

### 1.1 基本规则

- **前缀固定**：所有包必须以 `other` 开头

- **结构层级**：

  text

  ```
  other. + [公司标识] + [业务模块] + [功能类型]
  ```

  

- **公司标识**：

  - 使用公司域名（反序）或 `xsy`
  - 示例：`com.companyname` → `other.companyname.com`
  - 或直接使用：`other.xsy`

- **对象层级**：包名最后部分应为具体的业务对象或功能模块

### 1.2 标准示例

| 项目类型 | 正确示例                      | 错误示例                |
| :------- | :---------------------------- | :---------------------- |
| 客户管理 | `other.xsy.customer`          | `customer.other`        |
| 账户系统 | `other.rainbow.account`       | `account.rainbow.other` |
| 订单处理 | `other.companyname.com.order` | `order.other.company`   |

## 二、功能类分包规范

### 2.1 分包结构

text

```
src/main/java/other/[公司标识]/[模块]/
├── util/                    # 工具类
│   ├── DateUtils.java
│   ├── StringUtils.java
│   └── ValidatorUtils.java
├── service/                 # 接口类
│   ├── AccountService.java
│   └── OrderService.java
├── event/                   # 流程/事件类
│   ├── OrderCreatedEvent.java
│   └── PaymentProcessedEvent.java
├── trigger/                 # 触发器类
│   ├── AccountBeforeAddTrigger.java
│   └── OrderBeforeUpdateTrigger.java
├── futuretask/              # 异步任务
│   ├── ReportGenerationTask.java
│   └── DataSyncTask.java
├── batchJob/              # 批量任务
│   └── DailyReportBatchJob.java
└── schedule/                # 定时任务
│    ├── DailyReportSchedule.java
│    └── DataCleanupSchedule.java
└── pojo/                # 实体类
    └──ReceiptItemRow.java
```



### 2.2 各类职责说明

| 包名         | 功能说明                 | 命名规范           |
| :----------- | :----------------------- | :----------------- |
| `util`       | 通用工具方法，无业务状态 | `XxxUtils.java`    |
| `service`    | 业务接口定义             | `XxxService.java`  |
| `event`      | 业务流程事件处理         | `XxxEvent.java`    |
| `trigger`    | 数据操作触发器           | `XxxTrigger.java`  |
| `futuretask` | 异步执行任务             | `XxxTask.java`     |
| `schedule`   | 定时/计划任务            | `XxxSchedule.java` |
| `pojo`   | 实体类            | `Xxx.java` |
| `batchjob`   | 批量作业            | `XxxBatchJob.java` |

## 三、类规范

### 3.1 类命名通用规则

- **大小写规范**：大驼峰命名法（UpperCamelCase）
- **语义明确**：类名应准确反映其功能和业务含义
- **包名关联**：类名应包含包的关键信息

### 3.2 各类命名模板

| 类型     | 命名模板                           | 示例                           |
| :------- | :--------------------------------- | :----------------------------- |
| 接口类   | `[业务对象][功能]Service.java`     | `AccountToSapService.java`     |
| 触发器   | `[业务对象][触发时机]Trigger.java` | `AccountBeforeAddTrigger.java` |
| 工具类   | `[功能]Utils.java`                 | `DateConversionUtils.java`     |
| 事件类   | `[业务对象][动作]Event.java`       | `OrderCreatedEvent.java`       |
| 异步任务 | `[业务][操作]Task.java`            | `ReportExportTask.java`        |
| 定时任务 | `[周期][业务]Schedule.java`        | `DailyReportSchedule.java`     |
| 批量作业 | `[周期][业务]BatchJob.java`        | `DailyReportBatchJob.java` |
| 实体类 | `[业务对象].java`        | `ReceiptItemRow.java`     |

### 3.3 类命名禁止行为

- ❌ 使用缩写（除非是广泛认可的）
- ❌ 使用单字母或数字
- ❌ 包含下划线（除常量外）
- ❌ 与Java关键字冲突

### **3.4 类规范**

#### 3.4.1日志管理规范

- 日志级别统一
  - 建议统一使用info级别记录常规日志，避免过度依赖error或debug级别
  - try/catch 抛异常时需记录error日志，不应不记录直接抛出

#### 3.4.2 代码性能与结构优化

- 循环与条件嵌套优化
  - for循环嵌套过深(超过五层)的情况，建议将复杂逻辑抽离为独立方法以提高可读性
  - for循环中应优先使用continue控制流程，减少多层if判断带来的阅读困难
- 数据结构优化
  - 外层for循环内嵌另一个for循环进行数据比对的操作，建议改为构建Map结构以提升效率
  - 避免在for循环中执行数据库查询或DML操作，除非确有分页获取全量数据的需求

- 批处理

  - 存在分批处理室应评估未来大规模部署后的性能影响，必要时引入异步或batch处理机制
  
- 代码格式

- 代码缩进要保持一致的缩进量，if、for、while、do等语句尽量自占一行，执行语句不得紧跟其后，不论执行语句有多少都要加{}，这样可以美观易读防止书写失误； 

  使用以下写法

  ~~~java
  If (….){
  ​    //do something  
  }
  ~~~

  禁用

  ~~~java
  If (….)
  ​    //do something
  ~~~


- sql书写规范

  ~~~java
  String sql ="select " +
                      "id," +
                      "name," +
                      "username " +
              "from " +
                  "user";
  ~~~

  

#### 3.4.3 开发规范与可维护性

- ID与标识符使用
  - 禁止直接使用ID进行环境间查询，应使用记录类型名称查询ID
  - 如必需使用ID，应在类顶部声明为静态常量并加注释说明其含义
- 硬编码问题
  - 用户email等环境相关配置不应写死在代码中，建议移至自定义设置项中管理
- 状态值定义规范
  - 状态值(如status)不应直接使用数字或字符串字面量，应在类起始处定义为静态常量

#### 3.4.4 审批流与状态管理（针对审批流，若有业务流程如接口接回改变状态 不适用此规范）

- 状态变更方式
  - 所有初始和最终状态的变更均应通过审批流配置实现，不再允许在代码中手动修改
- 特殊情况处理
  - 对于已被锁定的对象(如审批完成后不可修改)，若需更新，可通过单独授权代码"后门"处理
  - 正常状态流转(如draft ==》approving)应完全由审批流驱动，无需代码干预

####     3.4.5 部署规范

- 所有部署操作必须通过部署包上线，不应直接修改生产环境



## 四、接口类注解规范

### 4.1 RestApi注解标准

```
/**
 * 账户同步接口服务
 * @author 张三
 * @version 1.0
 */
@RestApi(baseUrl = "/sync") // sync为包名
public interface AccountToSapService {
    
    /**
     * 同步账户信息到SAP系统
     * @param accountDTO 账户传输对象
     * @return 同步结果
     */
    @PostMapping("/syncToSap")
    ResponseResult<Boolean> syncAccountToSap(@RequestBody AccountDTO accountDTO);
    
    /**
     * 从SAP系统获取账户状态
     * @param accountId 账户ID
     * @return 账户状态信息
     */
    @GetMapping("/status/{accountId}")
    ResponseResult<AccountStatusVO> getAccountStatusFromSap(@PathVariable String accountId);
}
```



### 4.2 路径命名规范

| 包结构                    | 对应API路径                | 说明     |
| :------------------------ | :------------------------- | :------- |
| `other.xsy.account`       | `/other/xsy/account`       | 账户模块 |
| `other.company.com.order` | `/other/company/com/order` | 订单模块 |
| `other.rainbow.payment`   | `/other/rainbow/payment`   | 支付模块 |

## 五、代码注释规范

### 5.1 注释覆盖率要求

- **总体要求**：代码注释率 ≥ 75%，最低不能低于45%。
- **计算方法**：注释行数 / 总代码行数 × 100%

### 5.2 类级别注释模板

```
/**
 * 账户信息同步服务实现类
 * 
 * <p>该类负责处理账户数据向SAP系统的同步操作，包括：
 * <ul>
 *   <li>账户创建同步</li>
 *   <li>账户更新同步</li>
 *   <li>账户状态查询</li>
 * </ul>
 * 
 * @author 李四
 * @email lisi@company.com
 * @date 2024-01-15
 * @version 1.0.0
 * @since 1.0
 * @see AccountToSapService
 * @see AccountDTO
 */
@Service
public class AccountToSapServiceImpl implements AccountToSapService {
    // 类实现内容
}
```



### 5.3 方法注释规范

```
/**
 * 同步账户信息到SAP系统
 * 
 * <p><b>业务流程：</b></p>
 * <ol>
 *   <li>验证账户数据的完整性</li>
 *   <li>转换账户数据为SAP格式</li>
 *   <li>调用SAP接口进行数据同步</li>
 *   <li>处理同步结果并更新本地状态</li>
 * </ol>
 * 
 * <p><b>注意事项：</b></p>
 * <ul>
 *   <li>该方法为异步操作，实际同步结果通过事件通知</li>
 *   <li>同步失败时会进行最多3次重试</li>
 *   <li>单次同步超时时间为30秒</li>
 * </ul>
 * 
 * @param accountDTO 账户传输对象，包含账户基本信息
 *        <ul>
 *          <li>accountId - 账户ID，不能为空</li>
 *          <li>accountName - 账户名称，长度不超过100字符</li>
 *          <li>accountType - 账户类型，枚举值</li>
 *        </ul>
 * @return 同步操作结果
 *         <ul>
 *           <li>成功：返回包含同步ID的ResponseResult</li>
 *           <li>失败：返回错误码和错误信息</li>
 *         </ul>
 * @throws ValidationException 当账户数据验证失败时抛出
 * @throws SapConnectionException 当SAP系统连接异常时抛出
 * @throws BusinessException 当业务逻辑处理异常时抛出
 * 
 * @see AccountDTO
 * @see ResponseResult
 * @see AccountSyncEvent
 */
@Override
public ResponseResult<String> syncAccountToSap(AccountDTO accountDTO) 
        throws ValidationException, SapConnectionException, BusinessException {
    // 方法实现
}
```



### 5.4 代码逻辑注释

```
public class AccountValidator {
    
    /**
     * 验证账户信息的有效性
     */
    public boolean validateAccount(AccountDTO account) {
        // 步骤1: 基础信息非空校验
        if (StringUtils.isBlank(account.getAccountId())) {
            log.warn("账户ID不能为空");
            return false;
        }
        
        // 步骤2: 账户名称格式校验
        // 正则匹配：只允许中文、英文、数字和下划线
        String namePattern = "^[\\u4e00-\\u9fa5a-zA-Z0-9_]+$";
        if (!account.getAccountName().matches(namePattern)) {
            log.warn("账户名称包含非法字符: {}", account.getAccountName());
            return false;
        }
        
        // 步骤3: 账户类型枚举校验
        // 确保账户类型在允许的范围内
        if (!isValidAccountType(account.getAccountType())) {
            log.warn("无效的账户类型: {}", account.getAccountType());
            return false;
        }
        
        // 步骤4: 业务逻辑校验
        // 检查账户是否已存在且状态正常
        if (isAccountExists(account.getAccountId()) 
                && !isAccountActive(account.getAccountId())) {
            log.warn("账户已存在但状态异常: {}", account.getAccountId());
            return false;
        }
        
        return true;
    }
    
    /**
     * 检查账户类型是否有效
     * 
     * @param accountType 账户类型
     * @return true-有效，false-无效
     */
    private boolean isValidAccountType(String accountType) {
        return Arrays.asList("PERSONAL", "CORPORATE", "GOVERNMENT")
                     .contains(accountType);
    }
}
```



### 5.5 特殊注释标记

| 标记         | 含义           | 示例                                            |
| :----------- | :------------- | :---------------------------------------------- |
| `TODO`       | 待完成功能     | `// TODO: 需要添加缓存机制`                     |
| `FIXME`      | 需要修复的问题 | `// FIXME: 并发情况下可能存在问题`              |
| `NOTE`       | 重要说明       | `// NOTE: 此方法性能关键，勿随意修改`           |
| `OPTIMIZE`   | 优化建议       | `// OPTIMIZE: 可考虑使用线程池优化`             |
| `DEPRECATED` | 已过时方法     | `// DEPRECATED: 请使用新方法processAccountV2()` |

## 六、对象配置

命名中禁止出现无实际意义的命名，且需要遵循一定的规则。

### 6.1 **对象**

规范：把对象标签中的单词以首字母小写的方式连接起来，每个单词之前用“_”下划线连接。

示例：对象标签为**Weibo Account** ， 相对应的API名称应该为：**weibo_Account__c**。

### 6.2 **字段**

规范：用描述字段的英文单词连接，每个单词首字母小写，单词之间用“_”下划线连接。

示例：字段名称为**Weibo Account ID**，对应字段API名称为：**weibo_Account_ID__c**。

另外如果有Lookup类型的字段，一般使用引用的对象名作为字段名，如Weibo Account查找的是Account这个对象，那么字段名就应该为Account，子级关系名称就是当前这个对象的名称复数形式Weibo_Accounts，因为Weibo_Account__c是Account的子对象。

## 七、检查清单

### 7.1 代码提交前检查

- 包名是否符合 `other.[公司标识].[模块]` 格式
- 类是否放入正确的功能包中
- 类命名是否符合业务含义和规范
- 接口类是否有正确的 `@RestApi` 注解
- 代码注释率是否达到75%以上
- 所有公有方法是否有完整注释
- 复杂逻辑是否有详细说明
- 作者信息是否完整
- 异常处理是否有文档说明

### 7.2 代码审查要点

1. **结构规范性**

   - 包结构层次清晰
   - 类职责单一明确
   - 依赖关系合理

2. **命名可读性**

   - 名称反映真实功能
   - 遵循命名约定
   - 无歧义缩写

3. **文档完整性**

   - 接口契约明确
   - 业务流程清晰
   - 异常情况覆盖

4. **维护便利性**
   - 注释便于理解
   - 逻辑易于追踪
   - 扩展考虑充分

   

**通过遵循以上规范，可以确保代码的结构性、可读性和可维护性，同时便于团队协作和项目长期发展。**

