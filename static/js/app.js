/**
 * 版权管理系统 - 前端逻辑
 */

const { createApp, ref, computed, watch, onMounted, nextTick, onUnmounted } = Vue;

createApp({
    setup() {
        // 状态管理
        const currentPage = ref('dashboard');
        
        // 全局搜索
        const globalSearchKeyword = ref('');
        const globalSearchResults = ref([]);
        const showSearchResults = ref(false);
        
        // 模块搜索关键字
        const bookSearchKeyword = ref('');
        const contractSearchKeyword = ref('');
        const publisherSearchKeyword = ref('');
        const translatorSearchKeyword = ref('');
        
        // 统计数据
        const statistics = ref({
            total_books: 0,
            total_contracts: 0,
            total_translators: 0,
            total_foreign_publishers: 0,
            total_topic_ideas: 0,
            total_royalties: 0,
            books_by_status: {},
            contracts_by_status: {},
            topic_ideas_by_status: {}
        });
        
        // 提醒数据
        const reminders = ref([]);
        const reminderCounts = ref({ total: 0, contract_expiring: 0, topic_urgent: 0, topic_warning: 0 });
        
        // 数据列表
        const books = ref([]);
        const contracts = ref([]);
        const foreignPublishers = ref([]);
        const translators = ref([]);
        const topicIdeas = ref([]);
        const royalties = ref([]);
        
        // 枚举值
        const enums = ref({
            topicStatus: ['待洽谈', '洽谈中', '已签约', '已放弃'],
            bookStatus: ['意向阶段', '合同签约阶段', '翻译中', '编辑中', '已出版', '近期需续约', '已过期', '已废弃'],
            contractStatus: ['草稿', '已签约', '执行中', '已到期', '已作废'],
            royaltyType: ['统一版税率', '阶梯版税率'],
            validityType: ['签订日期开始', '出版日期开始'],
            firstPrintRequirement: ['数量', '无要求'],
            gender: ['男', '女'],
            translatorLevel: ['初级', '中级', '高级', '资深']
        });
        
        // 模态框状态
        const showModal = ref(false);
        const modalType = ref('');
        const modalTitle = ref('');
        const editingId = ref(null);
        const formData = ref({});
        
        // 阶梯版税档位数据
        const tieredTiers = ref([
            { min: 1, max: 5000, rate: '7' },
            { min: 5001, max: 10000, rate: '8' },
            { min: 10001, max: null, rate: '9' }
        ]);
        
        // 详情模态框
        const showDetailModal = ref(false);
        const detailData = ref(null);
        
        // 消息提示
        const showToast = ref(false);
        const toastMessage = ref('');
        const toastClass = ref('success');
        
        // 图表引用
        const bookChart = ref(null);
        const contractChart = ref(null);
        const topicChart = ref(null);
        
        // 计算属性
        const filteredBooks = computed(() => {
            if (!bookSearchKeyword.value) return books.value;
            const keyword = bookSearchKeyword.value.toLowerCase();
            return books.value.filter(book => 
                (book.publisher_name && book.publisher_name.toLowerCase().includes(keyword)) ||
                (book.contract_name && book.contract_name.toLowerCase().includes(keyword)) ||
                (book.publisher_country && book.publisher_country.toLowerCase().includes(keyword))
            );
        });
        
        const filteredContracts = computed(() => {
            if (!contractSearchKeyword.value) return contracts.value;
            const keyword = contractSearchKeyword.value.toLowerCase();
            return contracts.value.filter(contract => 
                (contract.contract_name && contract.contract_name.toLowerCase().includes(keyword)) ||
                (contract.foreign_publisher_name && contract.foreign_publisher_name.toLowerCase().includes(keyword))
            );
        });
        
        const filteredPublishers = computed(() => {
            if (!publisherSearchKeyword.value) return foreignPublishers.value;
            const keyword = publisherSearchKeyword.value.toLowerCase();
            return foreignPublishers.value.filter(publisher => 
                (publisher.original_name && publisher.original_name.toLowerCase().includes(keyword)) ||
                (publisher.chinese_name && publisher.chinese_name.toLowerCase().includes(keyword)) ||
                (publisher.country && publisher.country.toLowerCase().includes(keyword))
            );
        });
        
        const filteredTranslators = computed(() => {
            if (!translatorSearchKeyword.value) return translators.value;
            const keyword = translatorSearchKeyword.value.toLowerCase();
            return translators.value.filter(translator => 
                (translator.name && translator.name.toLowerCase().includes(keyword)) ||
                (translator.languages && translator.languages.toLowerCase().includes(keyword))
            );
        });
        
        // API基础路径
        const API_BASE = '/api';
        
        // 工具函数
        const api = {
            async get(url) {
                const res = await fetch(API_BASE + url);
                return res.json();
            },
            async post(url, data) {
                const res = await fetch(API_BASE + url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                return res.json();
            },
            async put(url, data) {
                const res = await fetch(API_BASE + url, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                return res.json();
            },
            async delete(url) {
                const res = await fetch(API_BASE + url, { method: 'DELETE' });
                return res.json();
            }
        };
        
        // 显示消息
        function showToastMessage(message, type = 'success') {
            toastMessage.value = message;
            toastClass.value = type;
            showToast.value = true;
            setTimeout(() => {
                showToast.value = false;
            }, 3000);
        }
        
        // 格式化日期
        function formatDate(dateStr) {
            if (!dateStr) return '-';
            const date = new Date(dateStr);
            return date.toLocaleDateString('zh-CN');
        }
        
        // 格式化字段名
        function formatFieldName(key) {
            const nameMap = {
                // 通用字段
                id: '编号',
                
                // 外版图书档案字段
                contract_id: '关联合同',
                publisher_name: '出版社名称',
                publisher_country: '出版社国家',
                book_number: '图字号',
                sample_sent: '样书已寄送',
                reference_price: '参考定价',
                actual_price: '实际定价',
                contract_reference_price: '合同参考定价',
                contract_actual_price: '合同实际定价',
                editor_sample_file: '编辑用样书',
                review_sample_file: '审阅用样书',
                quotation_file: '报价文件',
                contract_scan_file: '合同扫描件',
                countersign_file: '会签文件',
                translator_languages: '译者语种',
                book_status: '图书状态',
                
                // 合同管理字段
                contract_name: '合同名称',
                contract_file: '合同文件',
                countersign_file: '会签文件',
                chinese_translation_file: '中文译本',
                related_book_count: '关联图书数量',
                start_date: '开始日期',
                end_date: '结束日期',
                sign_date: '签订日期',
                validity_years: '有效期(年)',
                validity_type: '有效期类型',
                auto_renewal: '自动续约',
                agent_id: '代理商ID',
                commission_fee: '代理费',
                foreign_publisher_id: '外方出版社',
                authorization_scope: '授权范围',
                translator_id: '译者',
                advance_payment: '预付金',
                advance_paid: '预付金已支付',
                royalty_type: '版税类型',
                royalty_rate: '版税率',
                tiered_royalty: '阶梯版税配置',
                first_print_quantity: '首印量',
                first_print_requirement: '首印要求',
                editor_id: '编辑ID',
                contract_status: '合同状态',
                
                // 译者库字段
                name: '姓名',
                resume_file: '简历文件',
                languages: '语种',
                specialization: '专业领域',
                level: '级别',
                rate_per_thousand: '千字费率',
                contract_date: '合同日期',
                
                // 外商库字段
                original_name: '原名',
                chinese_name: '中文名',
                country: '国家',
                sample_book_received: '已收到样书',
                contact_name: '联系人姓名',
                contact_title: '联系人职位',
                contact_email: '联系人邮箱',
                has_multiple_contacts: '多联系人',
                
                // 意向选题库字段
                original_publisher_name: '外方出版社原名',
                chinese_publisher_name: '外方出版社中文名',
                author_name: '作者姓名',
                author_country: '作者国籍',
                author_gender: '作者性别',
                sample_file: '样书文件',
                intention_status: '意向状态',
                intention_date: '意向录入日期',
                
                // 版税管理字段
                book_id: '图书ID',
                advance_amount: '预付金金额',
                total_paid_amount: '累计支付金额',
                last_payment_date: '最近支付日期',
                tiered_structure: '阶梯版税结构',
                payment_cycle: '支付周期',
                report_date: '报表日期',
                payment_reminder: '收款提醒',
                
                // 通用字段
                remarks: '备注',
                created_at: '创建时间',
                updated_at: '更新时间',
                foreign_publisher_name: '外方出版社名称',
                translator_name: '译者姓名',
                translator_languages: '译者语种'
            };
            return nameMap[key] || key;
        }
        
        // 获取状态样式类
        function getStatusClass(status) {
            const classMap = {
                '待洽谈': 'pending',
                '洽谈中': 'negotiating',
                '已签约': 'signed',
                '已放弃': 'abandoned',
                '意向阶段': 'pending',
                '合同签约阶段': 'negotiating',
                '翻译中': 'negotiating',
                '编辑中': 'negotiating',
                '已出版': 'signed',
                '近期需续约': 'warning',
                '已过期': 'expired',
                '已废弃': 'abandoned'
            };
            return classMap[status] || '';
        }
        
        function getContractStatusClass(status) {
            const classMap = {
                '草稿': 'draft',
                '已签约': 'signed',
                '执行中': 'active',
                '已到期': 'expired',
                '已作废': 'void'
            };
            return classMap[status] || '';
        }
        
        // 数据加载
        async function loadStatistics() {
            try {
                const res = await api.get('/statistics');
                if (res.success) {
                    statistics.value = res.data;
                    await nextTick();
                    renderCharts();
                }
            } catch (e) {
                console.error('加载统计数据失败', e);
            }
        }
        
        async function loadReminders() {
            try {
                const res = await api.get('/reminders');
                if (res.success) {
                    reminders.value = res.data;
                    reminderCounts.value = res.counts;
                }
            } catch (e) {
                console.error('加载提醒失败', e);
            }
        }
        
        async function loadBooks() {
            try {
                const res = await api.get('/books');
                if (res.success) books.value = res.data;
            } catch (e) {
                console.error('加载图书失败', e);
            }
        }
        
        async function loadContracts() {
            try {
                const res = await api.get('/contracts');
                if (res.success) contracts.value = res.data;
            } catch (e) {
                console.error('加载合同失败', e);
            }
        }
        
        async function loadForeignPublishers() {
            try {
                const res = await api.get('/foreign-publishers');
                if (res.success) foreignPublishers.value = res.data;
            } catch (e) {
                console.error('加载外商失败', e);
            }
        }
        
        async function loadTranslators() {
            try {
                const res = await api.get('/translators');
                if (res.success) translators.value = res.data;
            } catch (e) {
                console.error('加载译者失败', e);
            }
        }
        
        async function loadTopicIdeas() {
            try {
                const res = await api.get('/topic-ideas');
                if (res.success) topicIdeas.value = res.data;
            } catch (e) {
                console.error('加载意向选题失败', e);
            }
        }
        
        async function loadRoyalties() {
            try {
                const res = await api.get('/royalties');
                if (res.success) royalties.value = res.data;
            } catch (e) {
                console.error('加载版税失败', e);
            }
        }
        
        async function loadEnums() {
            try {
                const res = await api.get('/enums');
                if (res.success) enums.value = res.data;
            } catch (e) {
                console.error('加载枚举值失败', e);
            }
        }
        
        // 加载所有数据
        async function loadAllData() {
            await Promise.all([
                loadStatistics(),
                loadReminders(),
                loadBooks(),
                loadContracts(),
                loadForeignPublishers(),
                loadTranslators(),
                loadTopicIdeas(),
                loadRoyalties(),
                loadEnums()
            ]);
        }
        
        // 渲染图表
        function renderCharts() {
            renderBookChart();
            renderContractChart();
            renderTopicChart();
        }
        
        function renderBookChart() {
            const chartDom = document.getElementById('bookChart') || document.querySelector('[ref="bookChart"]');
            if (!chartDom) return;
            
            const chart = echarts.init(chartDom);
            const data = statistics.value.books_by_status || {};
            const chartData = Object.keys(data).map(key => ({ name: key, value: data[key] }));
            
            chart.setOption({
                tooltip: { trigger: 'item' },
                legend: { bottom: '5%', left: 'center' },
                series: [{
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                    label: { show: false },
                    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
                    data: chartData.length > 0 ? chartData : [{ name: '暂无数据', value: 1 }],
                    color: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#000000']
                }]
            });
        }
        
        function renderContractChart() {
            const chartDom = document.getElementById('contractChart') || document.querySelector('[ref="contractChart"]');
            if (!chartDom) return;
            
            const chart = echarts.init(chartDom);
            const data = statistics.value.contracts_by_status || {};
            const chartData = Object.keys(data).map(key => ({ name: key, value: data[key] }));
            
            chart.setOption({
                tooltip: { trigger: 'item' },
                legend: { bottom: '5%', left: 'center' },
                series: [{
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                    label: { show: false },
                    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
                    data: chartData.length > 0 ? chartData : [{ name: '暂无数据', value: 1 }],
                    color: ['#d9d9d9', '#1890ff', '#52c41a', '#faad14', '#f5222d']
                }]
            });
        }
        
        function renderTopicChart() {
            const chartDom = document.getElementById('topicChart') || document.querySelector('[ref="topicChart"]');
            if (!chartDom) return;
            
            const chart = echarts.init(chartDom);
            const data = statistics.value.topic_ideas_by_status || {};
            const chartData = Object.keys(data).map(key => ({ name: key, value: data[key] }));
            
            chart.setOption({
                tooltip: { trigger: 'item' },
                legend: { bottom: '5%', left: 'center' },
                series: [{
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                    label: { show: false },
                    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
                    data: chartData.length > 0 ? chartData : [{ name: '暂无数据', value: 1 }],
                    color: ['#faad14', '#1890ff', '#52c41a', '#f5222d']
                }]
            });
        }
        
        // 模态框操作
        function openModal(type) {
            modalType.value = type;
            editingId.value = null;
            formData.value = {};
            
            // 初始化阶梯档位数据
            initTieredTiers();
            
            const titleMap = {
                book: '新增图书档案',
                contract: '新增合同',
                foreignPublisher: '新增外商',
                translator: '新增译者',
                topicIdea: '新增意向选题',
                royalty: '新增版税记录'
            };
            modalTitle.value = titleMap[type] || '新增';
            showModal.value = true;
        }
        
        function closeModal() {
            showModal.value = false;
            modalType.value = '';
            editingId.value = null;
            formData.value = {};
            // 重置阶梯档位数据
            initTieredTiers();
        }
        
        // 初始化阶梯版税档位数据
        function initTieredTiers() {
            tieredTiers.value = [
                { min: 1, max: 5000, rate: '7' },
                { min: 5001, max: 10000, rate: '8' },
                { min: 10001, max: null, rate: '9' }
            ];
        }
        
        // 添加阶梯档位
        function addTier() {
            const lastTier = tieredTiers.value[tieredTiers.value.length - 1];
            const newMin = lastTier ? (lastTier.max ? lastTier.max + 1 : lastTier.min + 1) : 1;
            tieredTiers.value.push({
                min: newMin,
                max: null,
                rate: ''
            });
        }
        
        // 删除阶梯档位
        function deleteTier(index) {
            if (tieredTiers.value.length > 1) {
                tieredTiers.value.splice(index, 1);
            }
        }
        
        // 解析阶梯版税数据（从JSON字符串解析为数组）
        function parseTieredRoyalty(jsonStr) {
            if (!jsonStr) return null;
            try {
                return JSON.parse(jsonStr);
            } catch (e) {
                console.error('解析阶梯版税数据失败', e);
                return null;
            }
        }
        
        // 序列化阶梯版税数据（从数组转为JSON字符串）
        function serializeTieredRoyalty() {
            return JSON.stringify(tieredTiers.value);
        }
        
        async function submitForm() {
            try {
                let res;
                const typeMap = {
                    book: '/books',
                    contract: '/contracts',
                    foreignPublisher: '/foreign-publishers',
                    translator: '/translators',
                    topicIdea: '/topic-ideas',
                    royalty: '/royalties'
                };
                const endpoint = typeMap[modalType.value];
                
                // 准备提交数据
                const submitData = { ...formData.value };
                
                // 如果是合同表单且选择阶梯版税率，序列化档位数据
                if (modalType.value === 'contract' && formData.value.royalty_type === '阶梯版税率') {
                    submitData.tiered_royalty = serializeTieredRoyalty();
                    submitData.royalty_rate = ''; // 阶梯版税时清空统一版税率
                } else if (modalType.value === 'contract' && formData.value.royalty_type === '统一版税率') {
                    submitData.tiered_royalty = ''; // 统一版税时清空阶梯版税
                }
                
                if (editingId.value) {
                    res = await api.put(`${endpoint}/${editingId.value}`, submitData);
                } else {
                    res = await api.post(endpoint, submitData);
                }
                
                if (res.success) {
                    showToastMessage(editingId.value ? '修改成功' : '添加成功');
                    closeModal();
                    loadAllData();
                } else {
                    showToastMessage(res.error || '操作失败', 'error');
                }
            } catch (e) {
                showToastMessage('操作失败: ' + e.message, 'error');
            }
        }
        
        async function editRecord(type, id) {
            modalType.value = type;
            editingId.value = id;
            
            const typeMap = {
                book: '/books',
                contract: '/contracts',
                foreignPublisher: '/foreign-publishers',
                translator: '/translators',
                topicIdea: '/topic-ideas',
                royalty: '/royalties'
            };
            const endpoint = typeMap[type];
            
            try {
                const res = await api.get(`${endpoint}/${id}`);
                if (res.success) {
                    formData.value = { ...res.data };
                    
                    // 如果是合同表单且有阶梯版税数据，解析并加载
                    if (type === 'contract' && res.data.tiered_royalty) {
                        const parsedTiers = parseTieredRoyalty(res.data.tiered_royalty);
                        if (parsedTiers && Array.isArray(parsedTiers) && parsedTiers.length > 0) {
                            tieredTiers.value = parsedTiers;
                        } else {
                            initTieredTiers();
                        }
                    } else if (type === 'contract') {
                        initTieredTiers();
                    }
                    
                    const titleMap = {
                        book: '编辑图书档案',
                        contract: '编辑合同',
                        foreignPublisher: '编辑外商',
                        translator: '编辑译者',
                        topicIdea: '编辑意向选题',
                        royalty: '编辑版税记录'
                    };
                    modalTitle.value = titleMap[type] || '编辑';
                    showModal.value = true;
                }
            } catch (e) {
                showToastMessage('获取数据失败', 'error');
            }
        }
        
        async function deleteRecord(table, id) {
            if (!confirm('确定要删除这条记录吗？')) return;
            
            try {
                const res = await api.delete(`/${table}/${id}`);
                if (res.success) {
                    showToastMessage('删除成功');
                    loadAllData();
                } else {
                    showToastMessage(res.error || '删除失败', 'error');
                }
            } catch (e) {
                showToastMessage('删除失败', 'error');
            }
        }
        
        async function viewDetail(type, id) {
            const typeMap = {
                book: '/books',
                contract: '/contracts',
                foreignPublisher: '/foreign-publishers',
                translator: '/translators',
                topicIdea: '/topic-ideas',
                royalty: '/royalties'
            };
            const endpoint = typeMap[type];
            
            try {
                const res = await api.get(`${endpoint}/${id}`);
                if (res.success) {
                    detailData.value = res.data;
                    showDetailModal.value = true;
                }
            } catch (e) {
                showToastMessage('获取详情失败', 'error');
            }
        }
        
        function closeDetailModal() {
            showDetailModal.value = false;
            detailData.value = null;
        }
        
        // 全局搜索处理
        let searchTimeout = null;
        async function handleGlobalSearch() {
            clearTimeout(searchTimeout);
            if (!globalSearchKeyword.value.trim()) {
                globalSearchResults.value = [];
                return;
            }
            searchTimeout = setTimeout(async () => {
                try {
                    const res = await api.get('/global-search?keyword=' + encodeURIComponent(globalSearchKeyword.value));
                    if (res.success) {
                        globalSearchResults.value = res.data;
                    }
                } catch (e) {
                    console.error('搜索失败', e);
                }
            }, 300);
        }
        
        // 跳转到搜索结果
        function navigateToResult(result) {
            showSearchResults.value = false;
            currentPage.value = result.type;
            nextTick(() => {
                viewDetail(result.type, result.id);
            });
        }
        
        // 点击空白处关闭搜索结果
        function handleClickOutside(event) {
            const searchContainer = document.querySelector('.global-search');
            if (searchContainer && !searchContainer.contains(event.target)) {
                showSearchResults.value = false;
            }
        }
        
        function searchBooks() {
            // 搜索通过计算属性自动处理
        }
        
        // 跳转到提醒对应的记录
        function goToReminder(reminder) {
            currentPage.value = reminder.module;
            nextTick(() => {
                if (reminder.record_id) {
                    editRecord(reminder.module === 'topicIdeas' ? 'topicIdea' : reminder.module.slice(0, -1), reminder.record_id);
                }
            });
        }
        
        // 文件上传函数
        async function uploadContractFile(contractId, event) {
            const file = event.target.files[0];
            if (!file) return;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const res = await fetch(API_BASE + '/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                if (data.success) {
                    // 更新合同记录
                    await api.put(`/contracts/${contractId}`, { contract_file: data.filename });
                    showToastMessage('合同文件上传成功');
                    // 刷新合同列表
                    await loadContracts();
                } else {
                    showToastMessage(data.error || '上传失败', 'error');
                }
            } catch (e) {
                showToastMessage('上传失败: ' + e.message, 'error');
            }
            event.target.value = '';
        }
        
        async function uploadBookFile(bookId, event) {
            const file = event.target.files[0];
            if (!file) return;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const res = await fetch(API_BASE + '/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                if (data.success) {
                    // 更新图书记录
                    await api.put(`/books/${bookId}`, { editor_sample_file: data.filename });
                    showToastMessage('样书文件上传成功');
                    // 刷新图书列表
                    await loadBooks();
                } else {
                    showToastMessage(data.error || '上传失败', 'error');
                }
            } catch (e) {
                showToastMessage('上传失败: ' + e.message, 'error');
            }
            event.target.value = '';
        }
        
        async function uploadTranslatorFile(translatorId, event) {
            const file = event.target.files[0];
            if (!file) return;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const res = await fetch(API_BASE + '/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                if (data.success) {
                    // 判断是简历还是合同（根据是否有现有文件）
                    const translator = translators.value.find(t => t.id === translatorId);
                    const updateData = translator && translator.resume_file 
                        ? { contract_file: data.filename } 
                        : { resume_file: data.filename };
                    // 更新译者记录
                    await api.put(`/translators/${translatorId}`, updateData);
                    showToastMessage('文件上传成功');
                    // 刷新译者列表
                    await loadTranslators();
                } else {
                    showToastMessage(data.error || '上传失败', 'error');
                }
            } catch (e) {
                showToastMessage('上传失败: ' + e.message, 'error');
            }
            event.target.value = '';
        }
        
        // 监听页面切换
        watch(currentPage, () => {
            nextTick(() => {
                if (currentPage.value === 'dashboard') {
                    renderCharts();
                }
            });
        });
        
        // 初始化
        onMounted(async () => {
            // 初始化数据库
            await api.post('/init', {});
            // 加载所有数据
            await loadAllData();
            // 添加点击空白处关闭搜索结果的事件监听
            document.addEventListener('click', handleClickOutside);
        });
        
        onUnmounted(() => {
            document.removeEventListener('click', handleClickOutside);
        });
        
        return {
            // 状态
            currentPage,
            globalSearchKeyword,
            globalSearchResults,
            showSearchResults,
            bookSearchKeyword,
            contractSearchKeyword,
            publisherSearchKeyword,
            translatorSearchKeyword,
            statistics,
            reminders,
            reminderCounts,
            books,
            contracts,
            foreignPublishers,
            translators,
            topicIdeas,
            royalties,
            enums,
            
            // 模态框
            showModal,
            modalType,
            modalTitle,
            editingId,
            formData,
            showDetailModal,
            detailData,
            
            // 阶梯版税
            tieredTiers,
            addTier,
            deleteTier,
            
            // 消息
            showToast,
            toastMessage,
            toastClass,
            
            // 图表
            bookChart,
            contractChart,
            topicChart,
            
            // 计算属性
            filteredBooks,
            filteredContracts,
            filteredPublishers,
            filteredTranslators,
            
            // 方法
            formatDate,
            formatFieldName,
            getStatusClass,
            getContractStatusClass,
            openModal,
            closeModal,
            submitForm,
            editRecord,
            deleteRecord,
            viewDetail,
            closeDetailModal,
            handleGlobalSearch,
            navigateToResult,
            searchBooks,
            goToReminder,
            uploadContractFile,
            uploadBookFile,
            uploadTranslatorFile
        };
    }
}).mount('#app');
