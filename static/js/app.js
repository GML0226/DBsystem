/**
 * AI LIMS - Frontend Application Logic
 * Built with Vanilla JavaScript
 */

const app = {
    // API Configuration
    api: {
        baseUrl: '',

        async request(endpoint, method = 'GET', data = null) {
            try {
                const options = { method, headers: { 'Content-Type': 'application/json' } };
                if (data) options.body = JSON.stringify(data);

                const response = await fetch(`${this.baseUrl}${endpoint}`, options);

                if (!response.ok) {
                    const error = await response.json();
                    let msg = '请求失败';
                    if (error.detail) {
                        msg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
                    }
                    throw new Error(msg);
                }
                return await response.json();
            } catch (error) {
                app.ui.toast(error.message, 'error');
                throw error;
            }
        }
    },

    // UI Utilities
    ui: {
        formatDate(dateStr) {
            if (!dateStr) return '--';
            const date = new Date(dateStr);
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
        },

        formatDateOnly(dateStr) {
            if (!dateStr) return '--';
            return dateStr.split('T')[0];
        },

        toast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;

            let icon = 'fa-check-circle';
            if (type === 'error') icon = 'fa-circle-xmark';
            if (type === 'warning') icon = 'fa-triangle-exclamation';

            toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
            container.appendChild(toast);

            setTimeout(() => {
                toast.style.animation = 'fadeOut 0.3s forwards';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        },

        // Navigation system with Micro-interactions (Transitions)
        initNav() {
            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (item.classList.contains('active')) return;

                    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                    item.classList.add('active');

                    const target = item.getAttribute('data-target');
                    const currentActive = document.querySelector('.page-section.active');
                    const targetEl = document.getElementById(target);

                    const enterAnimation = () => {
                        targetEl.classList.remove('hidden');
                        void targetEl.offsetWidth; // Force CSS reflow
                        targetEl.classList.add('active');

                        if (app[target] && typeof app[target].load === 'function') {
                            app[target].load();
                        }
                    };

                    if (currentActive) {
                        currentActive.classList.remove('active');
                        setTimeout(() => {
                            currentActive.classList.add('hidden');
                            enterAnimation();
                        }, 350); // wait for fade-out before showing next
                    } else {
                        document.querySelectorAll('.page-section').forEach(s => {
                            s.classList.remove('active');
                            s.classList.add('hidden');
                        });
                        enterAnimation();
                    }
                });
            });

            // Initial transition
            setTimeout(() => {
                const first = document.getElementById('dashboard'); // Default
                if (first) {
                    first.classList.remove('hidden');
                    void first.offsetWidth;
                    first.classList.add('active');
                }
            }, 100);

            // Responsive Menu Logic
            const menuBtn = document.getElementById('menu-toggle-btn');
            const sidebar = document.querySelector('.sidebar');
            if (menuBtn) {
                menuBtn.addEventListener('click', () => {
                    sidebar.classList.toggle('open');
                });
            }
            // Click outside to close
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 992 && sidebar.classList.contains('open')) {
                    if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
                        sidebar.classList.remove('open');
                    }
                }
            });
        },

        // --- Theme Switcher ---
        initTheme() {
            const savedTheme = localStorage.getItem('lab-theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            this.updateThemeIcon(savedTheme);
        },

        toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('lab-theme', newTheme);
            this.updateThemeIcon(newTheme);
            app.ui.toast(`已切换至${newTheme === 'dark' ? '深夜科技' : '纯净苹果'}模式`);

            // 刷新图谱色彩自适应
            if (app.graph && app.graph.chart) {
                app.graph.load();
            }
        },

        updateThemeIcon(theme) {
            const icon = document.getElementById('theme-icon');
            if (icon) {
                icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        },

        // --- Cursor Spotlight ---
        initSpotlight() {
            document.addEventListener('mousemove', e => {
                const cards = document.querySelectorAll('.spotlight-card');
                cards.forEach(card => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    card.style.setProperty('--mouse-x', `${x}px`);
                    card.style.setProperty('--mouse-y', `${y}px`);
                });
            });
        },

        // --- 3D Tilt Effect ---
        initTilt() {
            const cards = document.querySelectorAll('.stat-card');
            cards.forEach(card => {
                card.addEventListener('mousemove', e => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;

                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;

                    const percentX = (x - centerX) / centerX;
                    const percentY = (y - centerY) / centerY;

                    const rotateX = percentY * -10; // Max 10deg
                    const rotateY = percentX * 10;

                    card.style.transform = `perspective(1000px) scale(1.02) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                });

                card.addEventListener('mouseleave', () => {
                    card.style.transform = `perspective(1000px) scale(1) rotateX(0) rotateY(0)`;
                });
            });
        },

        // --- Skeleton Loading Helper ---
        setLoading(containerId, isLoading) {
            const container = document.getElementById(containerId);
            if (!container) return;
            if (isLoading) {
                container.setAttribute('data-old-html', container.innerHTML);
                container.innerHTML = `
                    <div class="skeleton" style="height: 100%; width: 100%; min-height: 100px; border-radius: 12px; background: rgba(0,0,0,0.03);">
                        <div class="skeleton-text" style="width: 60%; margin: 20px;"></div>
                        <div class="skeleton-text" style="width: 40%; margin: 20px;"></div>
                    </div>
                `;
            } else {
                const oldHtml = container.getAttribute('data-old-html');
                if (oldHtml) container.innerHTML = oldHtml;
            }
        },

        // --- Drawer (Legacy Modal Name for Compatibility) ---
        openModal(title, htmlContent, submitAction) {
            document.getElementById('modal-title').innerText = title;
            document.getElementById('modal-body').innerHTML = htmlContent;
            document.getElementById('common-modal').classList.add('active');
            app.currentSubmitAction = submitAction;
        },

        closeModal() {
            document.getElementById('common-modal').classList.remove('active');
            app.currentSubmitAction = null;
        },



        // --- Snowfall Effect ---
        initSnow() {
            const isSnowActive = localStorage.getItem('lab-snow') === 'true';
            if (isSnowActive) {
                this.toggleSnow(true);
            }
        },

        toggleSnow(forceState) {
            const container = document.getElementById('snow-container');
            const btn = document.getElementById('snow-btn');
            if (!container) return;

            const currentState = container.classList.contains('active');
            const newState = forceState !== undefined ? forceState : !currentState;

            if (newState) {
                container.classList.add('active');
                btn?.classList.add('btn-primary'); // 激活时高亮
                this.startSnowfall();
            } else {
                container.classList.remove('active');
                btn?.classList.remove('btn-primary');
                this.stopSnowfall();
            }
            localStorage.setItem('lab-snow', newState);
        },

        startSnowfall() {
            if (this.snowInterval) return;
            this.snowInterval = setInterval(() => {
                this.createSnowflake();
            }, 100); // 增加频率，营造大雪氛围
        },

        stopSnowfall() {
            clearInterval(this.snowInterval);
            this.snowInterval = null;
            // 逐渐清理现有雪花
            const container = document.getElementById('snow-container');
            if (container) setTimeout(() => container.innerHTML = '', 1000);
        },

        createSnowflake() {
            const container = document.getElementById('snow-container');
            if (!container || !container.classList.contains('active')) return;

            const flake = document.createElement('div');
            flake.className = 'snowflake';

            // 随机属性
            const size = Math.random() * 6 + 2 + 'px';
            const left = Math.random() * 100 + 'vw';
            const duration = Math.random() * 4 + 4 + 's';
            const opacity = Math.random() * 0.6 + 0.3;

            flake.style.width = size;
            flake.style.height = size;
            flake.style.left = left;
            flake.style.animationDuration = duration;
            flake.style.opacity = opacity;

            container.appendChild(flake);

            // 动画结束后移除
            setTimeout(() => {
                flake.remove();
            }, parseFloat(duration) * 1000);
        },

        confirmDelete(title, text, confirmAction) {
            Swal.fire({
                title: title,
                text: text,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: 'var(--danger)',
                cancelButtonColor: 'var(--secondary)',
                confirmButtonText: '确定删除',
                cancelButtonText: '取消',
                shape: 'border-radius: var(--radius-md)'
            }).then((result) => {
                if (result.isConfirmed) {
                    confirmAction();
                }
            });
        }
    },

    currentSubmitAction: null,
    modalSubmitHandler() {
        if (typeof app.currentSubmitAction === 'function') {
            const formData = new FormData(document.getElementById('common-form'));
            const data = Object.fromEntries(formData.entries());
            app.currentSubmitAction(data);
        }
    },

    // Global state
    state: {
        membersMap: {}, // id -> name mapping
        equipmentMap: {},
        consumablesMap: {},
        mentorsList: []
    },

    // Refresh Common Lookups
    async refreshLookups() {
        try {
            const [members, equip, consum] = await Promise.all([
                app.api.request('/members/'),
                app.api.request('/equipment/'),
                app.api.request('/inventory/consumables')
            ]);

            app.state.mentorsList = [];
            members.forEach(m => {
                app.state.membersMap[m.member_id] = m.name;
                if (m.role === 'Mentor') app.state.mentorsList.push(m);
            });

            equip.forEach(e => { app.state.equipmentMap[e.equipment_id] = e.name; });
            consum.forEach(c => { app.state.consumablesMap[c.consumable_id] = c.name; });

            // Build Auth Switcher
            const authSelect = document.getElementById('current-role-select');
            authSelect.innerHTML = members.map(m => `<option value="${m.member_id}">[${m.role}] ${m.name}</option>`).join('');

            // Build Dashboard Mentor Select
            const mentorSelect = document.getElementById('mentor-select');
            mentorSelect.innerHTML = '<option value="">-- 选择导师 --</option>' +
                app.state.mentorsList.map(m => `<option value="${m.member_id}">${m.name}</option>`).join('');

        } catch (e) {
            console.error("Failed to load lookups");
        }
    },

    // ==========================================
    // MODULE: Dashboard
    // ==========================================
    dashboard: {
        charts: {},
        async load() {
            try {
                // Show skeletons
                app.ui.setLoading('dash-eq-count', true);
                app.ui.setLoading('dash-mt-count', true);
                app.ui.setLoading('dash-rs-count', true);
                app.ui.setLoading('dash-wr-count', true);

                const [members, eq, reqs, warnings, maint, er] = await Promise.all([
                    app.api.request('/members/'),
                    app.api.request('/equipment/'),
                    app.api.request('/equipment/reservations/all'),
                    app.api.request('/api/dashboard/warnings'),
                    app.api.request('/api/dashboard/maintenance'),
                    app.api.request('/api/dashboard/equipment-ranking')
                ]);

                // Hide skeletons
                app.ui.setLoading('dash-eq-count', false);
                app.ui.setLoading('dash-mt-count', false);
                app.ui.setLoading('dash-rs-count', false);
                app.ui.setLoading('dash-wr-count', false);

                // 默认加载一季度的耗材排行榜
                this.loadConsumableRanking(90);

                // Top counters
                document.getElementById('dash-eq-count').innerText = eq.length;
                document.getElementById('dash-mt-count').innerText = maint.length;
                document.getElementById('dash-rs-count').innerText = reqs.length;
                document.getElementById('dash-wr-count').innerText = warnings.length;

                // Tables
                document.getElementById('dash-maintenance-table').innerHTML = maint.map(m => `
                    <tr>
                        <td style="font-weight: 500;">${m.name}</td>
                        <td><span class="status-badge badge-${m.status.toLowerCase()}">${m.status}</span></td>
                        <td>${m.current_usage_count} 次</td>
                        <td style="color:var(--danger); font-weight:600;">${m.max_usage_limit} 次</td>
                    </tr>
                `).join('') || '<tr><td colspan="4" style="text-align:center;">暂无需要维保的设备</td></tr>';

                document.getElementById('dash-warning-table').innerHTML = warnings.map(w => `
                    <tr>
                        <td style="color:var(--text-muted);">${app.ui.formatDate(w.created_at)}</td>
                        <td style="color:var(--danger); font-weight:500;"><i class="fas fa-circle-exclamation" style="margin-right:6px;"></i>${w.message}</td>
                    </tr>
                `).join('') || '<tr><td colspan="2" style="text-align:center;">无预警日志记录</td></tr>';

                // Initial selectors for insights
                const eqSelect = document.getElementById('insight-eq-select');
                eqSelect.innerHTML = '<option value="">-- 选择设备 --</option>' +
                    eq.map(e => `<option value="${e.equipment_id}">${e.name}</option>`).join('');

                const csSelect = document.getElementById('insight-cs-select');
                csSelect.innerHTML = '<option value="">-- 选择耗材 --</option>' +
                    eq.map(e => `<option value="${e.equipment_id}">${e.name}</option>`).join(''); // Wait, cr was used here before, let's fix this logic to use consumables list properly if possible

                // Fix: cr was the consumable ranking data, actually we should use inventory for insight select if we want it to be comprehensive
                const consumables = await app.api.request('/inventory/consumables');
                csSelect.innerHTML = '<option value="">-- 选择耗材 --</option>' +
                    consumables.map(c => `<option value="${c.consumable_id}">${c.name}</option>`).join('');

                this.renderEquipChart(er);

            } catch (e) { console.error('Dashboard load failed', e); }
        },

        async loadConsumableRanking(days) {
            try {
                const cr = await app.api.request(`/api/dashboard/consumable-ranking?days=${days}`);
                this.renderConsumableChart(cr);
            } catch (e) { console.error('Failed to load consumable ranking'); }
        },

        async loadEquipmentInsight() {
            const eqId = document.getElementById('insight-eq-select').value;
            if (!eqId) return;
            try {
                const data = await app.api.request(`/api/dashboard/equipment-insight/${eqId}`);
                document.getElementById('eq-insight-total').innerText = data.total_uses;
                document.getElementById('eq-insight-history').innerHTML = data.history.map(h => `
                    <tr>
                        <td>${h.member_name}</td>
                        <td>${app.ui.formatDate(h.start_time)}</td>
                        <td>${h.actual_return_time ? '<span style="color:var(--success);">已还</span>' : '<span style="color:var(--warning);">借用中</span>'}</td>
                    </tr>
                `).join('') || '<tr><td colspan="3" style="text-align:center;">暂无记录</td></tr>';
            } catch (e) { }
        },

        async loadConsumableDistribution() {
            const csId = document.getElementById('insight-cs-select').value;
            if (!csId) return;
            try {
                const data = await app.api.request(`/api/dashboard/consumable-distribution/${csId}`);
                this.renderConsumableDistChart(data);
            } catch (e) { }
        },

        renderConsumableDistChart(data) {
            if (!this.charts.cd) {
                this.charts.cd = echarts.init(document.getElementById('chart-consumable-dist'));
            }
            const option = {
                tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
                series: [{
                    type: 'pie',
                    radius: '65%',
                    center: ['50%', '50%'],
                    data: data.map(d => ({ name: d.member_name, value: d.total_quantity })),
                    emphasis: {
                        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
                    }
                }]
            };
            this.charts.cd.setOption(option);
        },

        renderEquipChart(data) {
            if (!this.charts.eq) {
                this.charts.eq = echarts.init(document.getElementById('chart-equipment'));
            }
            const option = {
                tooltip: { trigger: 'item' },
                color: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'],
                series: [{
                    name: '借阅次数',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                    label: { show: false, position: 'center' },
                    emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
                    labelLine: { show: false },
                    data: data.map(d => ({ name: d.name, value: d.borrow_count }))
                }]
            };
            this.charts.eq.setOption(option);
        },

        renderConsumableChart(data) {
            if (!this.charts.cs) {
                this.charts.cs = echarts.init(document.getElementById('chart-consumable'));
            }
            const option = {
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                grid: { top: 10, left: '3%', right: '4%', bottom: '3%', containLabel: true },
                xAxis: { type: 'value' },
                yAxis: { type: 'category', data: data.map(d => d.name).reverse() },
                series: [{
                    name: '消耗量',
                    type: 'bar',
                    data: data.map(d => d.total_consumed).reverse(),
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                            { offset: 0, color: '#10B981' },
                            { offset: 1, color: '#34D399' }
                        ]),
                        borderRadius: [0, 4, 4, 0]
                    }
                }]
            };
            this.charts.cs.setOption(option);
        },

        async loadMentorStats() {
            const mId = document.getElementById('mentor-select').value;
            if (!mId) return app.ui.toast('请先选择导师', 'warning');

            try {
                const data = await app.api.request(`/api/dashboard/mentor-stats/${mId}`);
                document.getElementById('mentor-eq-total').innerText = data.total_equipment_uses;
                document.getElementById('mentor-cs-total').innerText = data.total_consumable_used;
            } catch (e) { }
        }
    },

    // ==========================================
    // MODULE: Members
    // ==========================================
    members: {
        async load() {
            try {
                const data = await app.api.request('/members/');
                const tbody = document.getElementById('members-list');
                if (data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state"><i class="fas fa-users-slash"></i><p>暂无成员记录，点击“新增成员”开始</p></div></td></tr>`;
                    return;
                }
                tbody.innerHTML = data.map(m => `
                    <tr>
                        <td>#${m.member_id}</td>
                        <td style="font-weight: 500;">${m.name}</td>
                        <td>${m.role === 'Mentor' ? '<span class="status-badge badge-approved">导师</span>' : '<span class="status-badge badge-pending">学生</span>'}</td>
                        <td style="color:var(--text-muted);">${m.mentor_id ? (app.state.membersMap[m.mentor_id] || '') + ' (#' + m.mentor_id + ')' : '--'}</td>
                        <td style="text-align: right;">
                            <button class="btn btn-edit" onclick="app.members.openEditModal(${m.member_id})"><i class="fas fa-pen"></i></button>
                            <button class="btn btn-danger" onclick="app.members.delete(${m.member_id})"><i class="fas fa-trash"></i></button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { }
        },
        openModal() {
            const html = `
                <div class="form-group"><label>成员姓名</label><input type="text" name="name" required></div>
                <div class="form-group"><label>身份层级</label>
                    <select name="role"><option value="Student">学生</option><option value="Mentor">导师</option></select></div>
                <div class="form-group"><label>直属导师 ID (可选)</label><input type="number" name="mentor_id"></div>
            `;
            app.ui.openModal('新增成员配置', html, async (data) => {
                data.mentor_id = data.mentor_id ? parseInt(data.mentor_id) : null;
                await app.api.request('/members/', 'POST', data);
                app.ui.toast('成员已成功添加');
                app.ui.closeModal();
                this.load();
                app.refreshLookups();
            });
        },
        async openEditModal(id) {
            try {
                const m = await app.api.request(`/members/${id}`);
                const html = `
                    <div class="form-group"><label>成员姓名</label><input type="text" name="name" value="${m.name}" required></div>
                    <div class="form-group"><label>身份层级</label>
                        <select name="role">
                            <option value="Student" ${m.role === 'Student' ? 'selected' : ''}>学生</option>
                            <option value="Mentor" ${m.role === 'Mentor' ? 'selected' : ''}>导师</option>
                        </select></div>
                    <div class="form-group"><label>直属导师 ID (可选)</label><input type="number" name="mentor_id" value="${m.mentor_id || ''}"></div>
                `;
                app.ui.openModal(`编辑成员 #${id}`, html, async (data) => {
                    data.mentor_id = data.mentor_id ? parseInt(data.mentor_id) : null;
                    await app.api.request(`/members/${id}`, 'PUT', data);
                    app.ui.toast('成员已成功更新');
                    app.ui.closeModal();
                    this.load();
                    app.refreshLookups();
                });
            } catch (e) { }
        },
        delete(id) {
            app.ui.confirmDelete('确认移除此成员?', '此操作不可逆，将删除该记录', async () => {
                await app.api.request(`/members/${id}`, 'DELETE');
                app.ui.toast('已删除该成员');
                this.load();
                app.refreshLookups();
            });
        }
    },

    // ==========================================
    // MODULE: Equipment
    // ==========================================
    equipment: {
        async load() {
            try {
                const data = await app.api.request('/equipment/');
                const tbody = document.getElementById('equipment-list');
                if (data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i class="fas fa-microscope"></i><p>实验室尚未登记任何设备</p></div></td></tr>`;
                    return;
                }
                tbody.innerHTML = data.map(e => `
                    <tr>
                        <td>#${e.equipment_id}</td>
                        <td style="font-weight: 500;">${e.name}</td>
                        <td><span class="status-badge badge-${e.status.toLowerCase()}">${e.status}</span></td>
                        <td><span style="font-weight:700;">${e.current_usage_count}</span> 次</td>
                        <td>${e.max_usage_limit} 次</td>
                        <td style="text-align: right;">
                            <button class="btn btn-edit" title="维护与复位" onclick="app.equipment.openMaintainModal(${e.equipment_id})"><i class="fas fa-wrench"></i></button>
                            <button class="btn btn-danger" onclick="app.equipment.delete(${e.equipment_id})"><i class="fas fa-trash"></i></button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { }
        },
        openModal() {
            const html = `
                <div class="form-group"><label>设备名称</label><input type="text" name="name" required></div>
                <div class="form-group"><label>累计借用限额 (次)</label><input type="number" name="max_usage_limit" value="10" required></div>
                <div class="form-group"><label>基准启用日期</label><input type="date" name="last_maintenance_date" required></div>
            `;
            app.ui.openModal('入库新设备', html, async (data) => {
                data.max_usage_limit = parseInt(data.max_usage_limit);
                await app.api.request('/equipment/', 'POST', data);
                app.ui.toast('设备已成功记录');
                app.ui.closeModal();
                this.load();
                app.refreshLookups();
            });
        },
        async openMaintainModal(id) {
            const cu = document.getElementById('current-role-select').value;
            if (!cu) { return app.ui.toast('请先在顶栏选择操作用户', 'warning'); }

            const html = `
                <div class="form-group"><label>状态更新</label><select name="status">
                    <option value="Available">恢复可用 (Available) - 将清空计数</option>
                    <option value="Occupied">设为在用 (Occupied)</option>
                    <option value="Maintenance">设为维护 (Maintenance)</option>
                </select></div>
                <p style="font-size: 0.8rem; color: var(--danger); margin-bottom: 1rem;">* 注意：只有导师有权重置维保。恢复为 Available 会自动重置使用次数。</p>
            `;
            app.ui.openModal(`设备维护管理 #${id}`, html, async (data) => {
                await app.api.request(`/equipment/${id}?operator_id=${cu}`, 'PUT', data);
                app.ui.toast('状态已同步，计数已按规重置（若适用）');
                app.ui.closeModal();
                this.load();
            });
        },
        delete(id) {
            app.ui.confirmDelete('废弃该设备?', '记录将被清除！', async () => {
                await app.api.request(`/equipment/${id}`, 'DELETE');
                app.ui.toast('设备已彻底清除');
                this.load();
                app.refreshLookups();
            });
        }
    },

    // ==========================================
    // MODULE: Reservations
    // ==========================================
    reservations: {
        async load() {
            try {
                let url = '/equipment/reservations/all';
                const startTime = document.getElementById('reservation-start-time')?.value;
                const endTime = document.getElementById('reservation-end-time')?.value;
                
                const params = new URLSearchParams();
                if (startTime) params.append('start_time', startTime);
                if (endTime) params.append('end_time', endTime);
                
                if (params.toString()) {
                    url += `?${params.toString()}`;
                }

                const data = await app.api.request(url);
                const tbody = document.getElementById('reservations-list');
                if (data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><i class="fas fa-calendar-xmark"></i><p>当前无任何设备预约流水</p></div></td></tr>`;
                    return;
                }
                tbody.innerHTML = data.map(r => `
                    <tr>
                        <td>#${r.reservation_id}</td>
                        <td style="font-weight: 500; color: var(--primary);">${app.state.membersMap[r.member_id] || '未知'}</td>
                        <td style="font-weight: 500;">${app.state.equipmentMap[r.equipment_id] || '未知'}</td>
                        <td>${app.ui.formatDate(r.start_time)}</td>
                        <td>${app.ui.formatDate(r.end_time)}</td>
                        <td>${r.actual_return_time ? `<span style="color:var(--success); font-weight:500;">${app.ui.formatDate(r.actual_return_time)}</span>` : '<span style="color:var(--warning);">借用中</span>'}</td>
                        <td style="text-align: right;">
                            ${!r.actual_return_time ? `
                                <button class="btn btn-success btn-sm" onclick="app.reservations.returnMethod(${r.reservation_id})"><i class="fas fa-rotate-left"></i> 归还设备</button>
                            ` : ''}
                            <button class="btn btn-danger btn-sm" onclick="app.reservations.delete(${r.reservation_id})"><i class="fas fa-ban"></i> 撤销流水</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { }
        },
        openModal() {
            const cu = document.getElementById('current-role-select').value;
            if (!cu) { return app.ui.toast('请先在顶栏选择模拟测试用户', 'warning'); }

            // Build dynamic dropdown
            const eqOptions = Object.entries(app.state.equipmentMap).map(([id, name]) => `<option value="${id}">${name}</option>`).join('');

            const html = `
                <div class="form-group"><label>借预约用设备</label>
                    <select name="equipment_id" required>${eqOptions}</select></div>
                <div class="form-group"><label>借出时间</label><input type="datetime-local" name="start_time" required></div>
                <div class="form-group"><label>约定归还时间</label><input type="datetime-local" name="end_time" required></div>
            `;
            app.ui.openModal('预约中心', html, async (data) => {
                data.member_id = parseInt(cu);
                data.equipment_id = parseInt(data.equipment_id);
                // Simple ISODate conversion fix
                data.start_time = new Date(data.start_time).toISOString();
                data.end_time = new Date(data.end_time).toISOString();

                await app.api.request('/equipment/reserve', 'POST', data);

                app.ui.toast('借出操作已成功，计数已更新');
                app.ui.closeModal();
                this.load();
                app.equipment.load(); // 同步刷新设备状态
            });
        },
        async returnMethod(id) {
            try {
                await app.api.request(`/equipment/return/${id}`, 'POST');
                app.ui.toast('设备已归还，状态已恢复可用');
                this.load();
                app.equipment.load();
            } catch (e) { }
        },
        delete(id) {
            app.ui.confirmDelete('确认撤销流水?', '该预约流将被撤销。', async () => {
                await app.api.request(`/equipment/reservations/${id}`, 'DELETE');
                app.ui.toast('已删除');
                this.load();
            });
        }
    },

    // ==========================================
    // MODULE: Inventory
    // ==========================================
    inventory: {
        async load() {
            try {
                const data = await app.api.request('/inventory/consumables');
                const tbody = document.getElementById('inventory-list');
                if (data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state"><i class="fas fa-boxes-stacked"></i><p>耗材仓库空空如也</p></div></td></tr>`;
                    return;
                }
                tbody.innerHTML = data.map(c => `
                    <tr>
                        <td>#${c.consumable_id}</td>
                        <td style="font-weight: 500;">${c.name}</td>
                        <td><span style="font-size:1.1rem; color:${c.quantity < c.threshold ? 'var(--danger)' : 'var(--text-main)'}; font-weight:700;">${c.quantity}</span></td>
                        <td style="color:var(--text-muted);">${c.threshold}</td>
                        <td style="text-align: right;">
                            <button class="btn btn-edit" onclick="app.inventory.openEditModal(${c.consumable_id}, '${c.name}', ${c.quantity}, ${c.threshold})"><i class="fas fa-layer-group"></i> 调节</button>
                            <button class="btn btn-danger" onclick="app.inventory.delete(${c.consumable_id})"><i class="fas fa-trash"></i></button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { }
        },
        openModal() {
            const html = `
                <div class="form-group"><label>耗材类别</label><input type="text" name="name" required></div>
                <div class="form-group"><label>实物库存总量</label><input type="number" name="quantity" required></div>
                <div class="form-group"><label>告警红线</label><input type="number" name="threshold" required></div>
            `;
            app.ui.openModal('建立耗材档案', html, async (data) => {
                data.quantity = parseInt(data.quantity);
                data.threshold = parseInt(data.threshold);
                await app.api.request('/inventory/consumables', 'POST', data);
                app.ui.toast('库存类库已建立');
                app.ui.closeModal();
                this.load();
                app.refreshLookups();
            });
        },
        openEditModal(id, name, q, t) {
            const html = `
                <div class="form-group"><label>名目重装 (可选)</label><input type="text" name="name" value="${name}"></div>
                <div class="form-group"><label>现余可用储备修正</label><input type="number" name="quantity" value="${q}"></div>
                <div class="form-group"><label>告警红线</label><input type="number" name="threshold" value="${t}"></div>
            `;
            app.ui.openModal(`动态盘点 #${id}`, html, async (data) => {
                data.quantity = parseInt(data.quantity);
                data.threshold = parseInt(data.threshold);
                await app.api.request(`/inventory/consumables/${id}`, 'PUT', data);
                app.ui.toast('库存已核准');
                app.ui.closeModal();
                this.load();
            });
        },
        delete(id) {
            app.ui.confirmDelete('移除该条目?', '库项清除不可逆。', async () => {
                await app.api.request(`/inventory/consumables/${id}`, 'DELETE');
                app.ui.toast('已删除');
                this.load();
                app.refreshLookups();
            });
        }
    },

    // ==========================================
    // MODULE: Requisitions (审批流)
    // ==========================================
    requisitions: {
        async load() {
            try {
                let url = '/inventory/requisitions';
                const startTime = document.getElementById('requisition-start-time')?.value;
                const endTime = document.getElementById('requisition-end-time')?.value;
                
                const params = new URLSearchParams();
                if (startTime) params.append('start_time', startTime);
                if (endTime) params.append('end_time', endTime);
                
                if (params.toString()) {
                    url += `?${params.toString()}`;
                }

                const data = await app.api.request(url);
                // Order by apply_date desc roughly
                data.sort((a, b) => b.requisition_id - a.requisition_id);
                const tbody = document.getElementById('requisitions-list');
                tbody.innerHTML = data.map(r => `
                    <tr>
                        <td>#${r.requisition_id}</td>
                        <td style="font-weight: 500; color: var(--primary);">${app.state.membersMap[r.member_id] || '未知'}</td>
                        <td style="font-weight: 500;">${app.state.consumablesMap[r.consumable_id] || '未知'}</td>
                        <td style="font-weight: 700;">x ${r.quantity}</td>
                        <td style="font-size: 0.85rem;">${app.ui.formatDate(r.apply_date)}</td>
                        <td><span class="status-badge badge-${r.status.toLowerCase()}">${r.status}</span></td>
                        <td style="text-align: right;">
                            ${r.status === 'Pending' ? `
                                <button class="btn btn-success btn-sm" onclick="app.requisitions.handle(${r.requisition_id}, 'Approved')" style="padding:0.3rem 0.6rem;font-size:0.8rem;"><i class="fas fa-check"></i> 同意</button>
                                <button class="btn btn-danger btn-sm" onclick="app.requisitions.handle(${r.requisition_id}, 'Rejected')" style="padding:0.3rem 0.6rem;font-size:0.8rem;"><i class="fas fa-times"></i> 驳回</button>
                            ` : `<button class="btn btn-danger btn-sm" onclick="app.requisitions.delete(${r.requisition_id})" style="padding:0.3rem 0.6rem;font-size:0.8rem;"><i class="fas fa-trash"></i></button>`}
                        </td>
                    </tr>
                `).join('');
            } catch (e) { }
        },
        openModal() {
            const cu = document.getElementById('current-role-select').value;
            if (!cu) { return app.ui.toast('请先在顶栏选择测试用户', 'warning'); }

            const csOptions = Object.entries(app.state.consumablesMap).map(([id, name]) => `<option value="${id}">${name}</option>`).join('');
            const html = `
                <div class="form-group"><label>欲领用耗材</label><select name="consumable_id" required>${csOptions}</select></div>
                <div class="form-group"><label>申请数量规模</label><input type="number" name="quantity" required min="1"></div>
            `;
            app.ui.openModal('递签申领清单', html, async (data) => {
                data.member_id = parseInt(cu);
                data.consumable_id = parseInt(data.consumable_id);
                data.quantity = parseInt(data.quantity);
                data.status = "Pending";
                await app.api.request('/inventory/requisitions', 'POST', data);

                app.ui.toast('申领卷宗已流转至系统审核！');
                app.ui.closeModal();
                this.load();
            });
        },
        async handle(id, status) {
            const cu = document.getElementById('current-role-select').value;
            if (!cu) { return app.ui.toast('请先在顶栏选择操作用户', 'warning'); }

            Swal.fire({
                title: status === 'Approved' ? '决定放行物资?' : '确认驳回该请求?',
                text: status === 'Approved' ? '只有导师可以操作流转！放行将直接触发库存系统的总类账扣罚及阈值告警！' : '只有导师有权驳回。',
                icon: status === 'Approved' ? 'info' : 'warning',
                showCancelButton: true,
                confirmButtonColor: status === 'Approved' ? '#10B981' : '#EF4444',
                confirmButtonText: '确定审核',
                cancelButtonText: '暂缓'
            }).then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        await app.api.request(`/inventory/requisitions/${id}?operator_id=${cu}`, 'PUT', { status });
                        app.ui.toast(status === 'Approved' ? '物资通过放行，可检出控制台警报' : '申领被拦截回退');
                        this.load();
                    } catch (e) { }
                }
            });
        },
        delete(id) {
            app.ui.confirmDelete('抹去流水史?', '审批档底将被永久撤除。', async () => {
                await app.api.request(`/inventory/requisitions/${id}`, 'DELETE');
                app.ui.toast('历史已清毁');
                this.load();
            });
        }
    },

    // ==========================================
    // MODULE: AI Analysis
    // ==========================================
    ai: {
        handleProviderChange() {
            const provider = document.getElementById('ai-provider-select').value;
            const baseUrlContainer = document.getElementById('ai-baseurl-container');
            const baseUrlInput = document.getElementById('ai-base-url');
            const modelSelect = document.getElementById('ai-model-select');

            // 重置模型选择框
            modelSelect.innerHTML = '<option value="">-- 请先点击右侧刷新拉取模型 --</option>';

            if (provider === 'gemini') {
                baseUrlContainer.style.display = 'none';
                modelSelect.innerHTML = '<option value="models/gemini-1.5-pro">Gemini 1.5 Pro (推荐)</option>';
            } else if (provider === 'siliconflow') {
                baseUrlContainer.style.display = 'block';
                baseUrlInput.value = 'https://api.siliconflow.cn/v1';
            } else if (provider === 'openai') {
                baseUrlContainer.style.display = 'block';
                baseUrlInput.value = ''; // 待用户填写
                baseUrlInput.placeholder = 'https://api.example.com/v1';
            }
        },

        async fetchModels() {
            const key = document.getElementById('ai-api-key').value;
            const providerSelect = document.getElementById('ai-provider-select').value;
            let provider = providerSelect === 'siliconflow' ? 'openai' : providerSelect;
            const baseUrl = document.getElementById('ai-base-url').value;

            if (!key) return app.ui.toast('请先输入 API Key', 'warning');

            // 如果是非 Gemini，且未填写 Base URL
            if (provider === 'openai' && !baseUrl) {
                return app.ui.toast('请先填写 Base URL', 'warning');
            }

            const btn = document.querySelector('#ai-model-select').nextElementSibling;
            const select = document.getElementById('ai-model-select');

            try {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

                let url = `/api/ai/models?api_key=${encodeURIComponent(key)}&provider=${provider}`;
                if (provider === 'openai') {
                    url += `&base_url=${encodeURIComponent(baseUrl)}`;
                }

                const models = await app.api.request(url, 'GET');

                if (models && models.length > 0) {
                    // 优先展示更高级的模型
                    models.sort((a, b) => b.display_name.localeCompare(a.display_name));

                    select.innerHTML = models.map(m =>
                        `<option value="${m.id}">${m.display_name}</option>`
                    ).join('');

                    app.ui.toast(`成功拉取 ${models.length} 个可用模型`);
                } else {
                    app.ui.toast('未找到支持文本生成的模型', 'warning');
                }
            } catch (e) {
                app.ui.toast('模型拉取失败，请检查 API Key', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-rotate"></i>';
            }
        },

        async runAnalysis(event) {
            const modelId = document.getElementById('ai-model-select').value;
            const key = document.getElementById('ai-api-key').value;
            const prompt = document.getElementById('ai-prompt-template').value;
            const analysisPeriod = document.getElementById('ai-analysis-period').value;
            const providerSelect = document.getElementById('ai-provider-select').value;
            let provider = providerSelect === 'siliconflow' ? 'openai' : providerSelect;
            const baseUrl = document.getElementById('ai-base-url').value;

            if (!key) return app.ui.toast('请输入 API Key', 'warning');
            if (!modelId) return app.ui.toast('请选择分析模型', 'warning');
            if (provider === 'openai' && !baseUrl) return app.ui.toast('请填写 Base URL', 'warning');

            const btn = document.querySelector('#ai button');
            const status = document.getElementById('ai-status');
            const resultArea = document.getElementById('ai-result-content');

            try {
                // UI Loading state
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在提取数据并分析中...';
                status.innerText = '正在调取实验室全维度数据...';
                resultArea.innerHTML = `
                    <div class="flex-center ai-loading-pulse" style="height: 100%; flex-direction: column; gap: 1rem;">
                        <i class="fas fa-microchip" style="font-size: 3rem; color: var(--primary);"></i>
                        <p>AI 正在深度思考中，请稍候... (预计需要 15-30s)</p>
                    </div>
                `;

                const response = await app.api.request('/api/ai/analyze', 'POST', {
                    provider: provider,
                    base_url: provider === 'openai' ? baseUrl : null,
                    model_id: modelId,
                    api_key: key,
                    prompt_template: prompt,
                    analysis_period: analysisPeriod
                });

                status.innerText = '分析完成';
                this.renderMarkdown(response.analysis, resultArea);
                app.ui.toast('AI 智能分析报告已生成');

            } catch (e) {
                status.innerText = '分析失败';
                resultArea.innerHTML = `
                    <div class="flex-center" style="height: 100%; color: var(--danger); flex-direction: column; gap: 1rem;">
                        <i class="fas fa-circle-exclamation" style="font-size: 3rem;"></i>
                        <p>分析出错: ${e.message}</p>
                    </div>
                `;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-wand-magic-sparkles"></i> 再次执行智能分析';
            }
        },

        // 完整 Markdown 渲染器实现
        renderMarkdown(text, container) {
            if (typeof marked !== 'undefined') {
                container.innerHTML = marked.parse(text);
            } else {
                // 回退方案
                container.innerHTML = '<p>' + text.replace(/\n/g, '<br>') + '</p>';
            }
        },

        copyResult() {
            const content = document.getElementById('ai-result-content').innerText;
            if (content.includes('待执行分析')) return app.ui.toast('暂无内容可复制', 'warning');

            navigator.clipboard.writeText(content).then(() => {
                app.ui.toast('报告内容已复制到剪贴板');
            });
        }
    },

    // ==========================================
    // MODULE: Knowledge Graph
    // ==========================================
    graph: {
        chart: null,
        async load() {
            const query = document.getElementById('graph-search-input').value;
            const container = document.getElementById('chart-kg-container');
            if (!container) return;

            try {
                if (!this.chart) {
                    this.chart = echarts.init(container);
                }
                this.chart.resize(); // 确保容器比例调整后即时刷新尺寸
                this.chart.showLoading({ text: '正在织造关系网...', color: 'var(--primary)', textColor: 'var(--text-main)', maskColor: 'rgba(255, 255, 255, 0.2)' });

                const data = await app.api.request(`/api/graph/search?q=${encodeURIComponent(query)}`);

                const option = {
                    title: {
                        text: query ? `关键词 "${query}" 的关联图谱` : '实验室全维度关系概览',
                        bottom: 20, right: 20,
                        textStyle: { color: 'var(--text-muted)', fontSize: 12, fontWeight: 'normal' }
                    },
                    tooltip: {
                        trigger: 'item',
                        formatter: (params) => {
                            if (params.dataType === 'node') {
                                return `<div style="padding:5px;"><b>${params.name}</b><br/>类型: ${params.data.category}</div>`;
                            }
                            const relMap = { 'BORROWED': '借用关系', 'CONSUMED': '领用消耗', 'MENTOR_OF': '师生/指导' };
                            return `<div style="padding:5px;"><b>${relMap[params.data.rel] || params.data.rel}</b><br/>关联强度: ${params.data.weight}</div>`;
                        }
                    },
                    legend: [{
                        data: ['member', 'equipment', 'consumable'],
                        orient: 'vertical', left: 20, top: 20,
                        textStyle: { color: 'var(--text-main)' }
                    }],
                    series: [{
                        type: 'graph',
                        layout: 'force',
                        data: data.nodes.map(n => ({
                            id: n.id,
                            name: n.name,
                            symbolSize: n.val * 1.5 + 10,
                            category: n.type,
                            value: n.val,
                            draggable: true,
                            itemStyle: {
                                color: n.type === 'member' ? '#af52de' : (n.type === 'equipment' ? '#34c759' : '#ff9f0a'),
                                shadowBlur: 15,
                                shadowColor: 'rgba(0,0,0,0.15)',
                                borderWidth: 2,
                                borderColor: 'rgba(255,255,255,0.8)'
                            }
                        })),
                        links: data.links.map(l => ({
                            source: l.source,
                            target: l.target,
                            rel: l.label, // 存储关系文本
                            weight: l.weight,
                            label: { show: false }, // 线上不强制常驻显示，通过悬浮查看
                            lineStyle: { width: Math.min(l.weight, 10), curveness: 0.2, opacity: 0.4 }
                        })),
                        categories: [
                            { name: 'member', itemStyle: { color: '#af52de' } },
                            { name: 'equipment', itemStyle: { color: '#34c759' } },
                            { name: 'consumable', itemStyle: { color: '#ff9f0a' } }
                        ],
                        roam: true,
                        label: {
                            show: true,
                            position: 'right',
                            fontSize: 11,
                            fontWeight: '600',
                            color: document.documentElement.getAttribute('data-theme') === 'dark' ? '#fff' : '#1d1d1f',
                            textBorderColor: document.documentElement.getAttribute('data-theme') === 'dark' ? 'rgba(0,0,0,0.8)' : 'rgba(255,255,255,0.8)',
                            textBorderWidth: 3,
                            distance: 10
                        },
                        force: {
                            repulsion: 1500,
                            edgeLength: [150, 350],
                            gravity: 0.01, // 极低引力，允许节点向四周（尤其是侧边）扩散
                            layoutAnimation: true,
                            friction: 0.6 // 稍大的摩擦力让布局更稳定，避免剧烈晃动
                        },
                        emphasis: {
                            focus: 'adjacency',
                            lineStyle: { width: 6, opacity: 1, color: 'var(--primary)' },
                            label: {
                                show: true,
                                fontSize: 13,
                                textBorderWidth: 4
                            }
                        }
                    }]
                };

                this.chart.hideLoading();
                this.chart.setOption(option);

                this.chart.on('click', (params) => {
                    if (params.dataType === 'node') {
                        app.ui.toast(`已定位至: ${params.name}`, 'info');
                    }
                });

            } catch (e) {
                if (this.chart) this.chart.hideLoading();
                console.error('Graph load failed', e);
            }
        },
        reset() {
            document.getElementById('graph-search-input').value = '';
            this.load();
        }
    },

    // Bootstrap
    async init() {
        app.ui.initTheme(); // Load saved theme
        app.ui.initSnow();  // Load snow state
        app.ui.initNav();
        app.ui.initSpotlight();
        app.ui.initTilt();

        await app.refreshLookups();
        app.dashboard.load();

        // Setup resize for charts
        window.addEventListener('resize', () => {
            if (app.dashboard.charts.eq) app.dashboard.charts.eq.resize();
            if (app.dashboard.charts.cs) app.dashboard.charts.cs.resize();
            if (app.dashboard.charts.cd) app.dashboard.charts.cd.resize();
            if (app.graph.chart) app.graph.chart.resize();
        });
    }
};

// Start application
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
