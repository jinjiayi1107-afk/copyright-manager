/**
 * 版权管理系统 - 前端逻辑
 */

const { createApp, ref, computed, watch, onMounted, nextTick } = Vue;

createApp({
    setup() {
        // 状态管理
        const currentPage = ref('dashboard');
        const searchKeyword = ref('');
        
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
            if (!searchKeyword.value) return books.value;
            const keyword = searchKeyword.value.toLowerCase();
            return books.value.filter(book => 
                (book.publisher_name && book.publisher_name.toLowerCase().includes(keyword)) ||
                (book.contract_name && book.contract_name.toLowerCase().includes(keyword))
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
                id: 'ID',
                original_name: '外文名称',
                chinese_name: '中文名称',
                country: '国家',
                publisher_name: '出版社名称',
                publisher_country: '出版社国家',
                contract_name: '合同名称',
                contract_id: '合同ID',
                book_id: '图书ID',
                author_name: '作者姓名',
                author_country: '作者国籍',
                author_gender: '作者性别',
                reference_price: '参考定价',
                actual_price: '实际定价',
                book_status: '图书状态',
                contract_status: '合同状态',
                intention_status: '意向状态',
                intention_date: '意向录入日期',
                sign_date: '合同签订日期',
                start_date: '起始日期',
                end_date: '结束日期',
                validitY_years: '有效期(年)',
                validity_type: '有效期计算方式',
                royalty_type: '版税类型',
                royalty_rate: '版税率',
                advance_amount: '预付金金额',
                advance_payment: '预付金',
                advance_paid: '预付金已支付',
                total_paid_amount: '累计支付金额',
                last_payment_date: '最近支付日期',
                languages: '擅长语种',
                specialization: '擅长领域',
                level: '译者分级',
                rate_per_thousand: '报价(元/千字)',
                contact_name: '联系人姓名',
                contact_title: '联系人职位',
                contact_email: '联系人邮箱',
                contact_info: '联系方式',
                related_book_count: '关联图书数量',
                first_print_quantity: '首印量',
                book_number: '图字号',
                remarks: '备注',
                created_at: '创建时间',
                updated_at: '更新时间',
                original_publisher_name: '外方出版社原名',
                chinese_publisher_name: '外方出版社中文名',
                foreign_publisher_name: '外方出版社名称',
                translator_id: '译者ID',
                translator_name: '译者姓名',
                translator_languages: '译者语种',
                sample_sent: '已寄送外方样书',
                payment_reminder: '收款提醒'
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
                
                if (editingId.value) {
                    res = await api.put(`${endpoint}/${editingId.value}`, formData.value);
                } else {
                    res = await api.post(endpoint, formData.value);
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
        });
        
        return {
            // 状态
            currentPage,
            searchKeyword,
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
            searchBooks,
            goToReminder,
            uploadContractFile,
            uploadBookFile,
            uploadTranslatorFile
        };
    }
}).mount('#app');
