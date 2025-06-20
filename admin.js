// VideoBot Admin Panel JavaScript

class AdminPanel {
    constructor() {
        this.apiBase = '/api';
        this.currentSection = 'dashboard';
        this.charts = {};
        this.init();
    }

    init() {
        this.setupNavigation();
        this.loadDashboard();
        this.setupEventListeners();
    }

    setupNavigation() {
        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.showSection(section);
                
                // Update active nav
                document.querySelectorAll('.sidebar .nav-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    setupEventListeners() {
        // Search functionality
        document.getElementById('user-search')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchUsers();
            }
        });

        // Sales period change
        document.getElementById('sales-period')?.addEventListener('change', () => {
            this.loadSalesData();
        });
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
            targetSection.classList.add('fade-in');
            this.currentSection = sectionName;

            // Load section data
            this.loadSectionData(sectionName);
        }
    }

    loadSectionData(section) {
        switch (section) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'products':
                this.loadProducts();
                break;
            case 'sales':
                this.loadSalesData();
                break;
            case 'downloads':
                this.loadDownloads();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    }

    async loadDashboard() {
        try {
            // Load stats
            const statsResponse = await fetch(`${this.apiBase}/stats`);
            const stats = await statsResponse.json();

            if (stats.status === 'success') {
                document.getElementById('total-products').textContent = stats.stats.total_products || 0;
                document.getElementById('total-sales').textContent = stats.stats.total_sales || 0;
                document.getElementById('total-revenue').textContent = stats.stats.total_revenue || 0;
                document.getElementById('total-users').textContent = stats.stats.total_users || 0;
            }

            // Load charts
            this.loadSalesChart();
            this.loadProductsChart();
            this.loadRecentActivity();

        } catch (error) {
            console.error('Erro ao carregar dashboard:', error);
            this.showError('Erro ao carregar dados do dashboard');
        }
    }

    async loadSalesChart() {
        try {
            const ctx = document.getElementById('salesChart');
            if (!ctx) return;

            // Dados simulados - substituir por dados reais da API
            const data = {
                labels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
                datasets: [{
                    label: 'Vendas',
                    data: [12, 19, 3, 5, 2, 3, 8],
                    borderColor: 'rgb(13, 110, 253)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4
                }]
            };

            if (this.charts.sales) {
                this.charts.sales.destroy();
            }

            this.charts.sales = new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Erro ao carregar gráfico de vendas:', error);
        }
    }

    async loadProductsChart() {
        try {
            const ctx = document.getElementById('productsChart');
            if (!ctx) return;

            // Dados simulados
            const data = {
                labels: ['Produto A', 'Produto B', 'Produto C'],
                datasets: [{
                    data: [30, 25, 45],
                    backgroundColor: [
                        'rgba(13, 110, 253, 0.8)',
                        'rgba(25, 135, 84, 0.8)',
                        'rgba(255, 193, 7, 0.8)'
                    ]
                }]
            };

            if (this.charts.products) {
                this.charts.products.destroy();
            }

            this.charts.products = new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Erro ao carregar gráfico de produtos:', error);
        }
    }

    async loadRecentActivity() {
        try {
            const container = document.getElementById('recent-activity');
            
            // Dados simulados
            const activities = [
                { type: 'sale', message: 'Nova venda: Produto A por 50 Stars', time: '2 min atrás' },
                { type: 'download', message: 'Download realizado: Produto B', time: '5 min atrás' },
                { type: 'user', message: 'Novo usuário cadastrado: @usuario123', time: '10 min atrás' }
            ];

            const html = activities.map(activity => `
                <div class="d-flex align-items-center mb-3">
                    <div class="me-3">
                        <i class="fas fa-${this.getActivityIcon(activity.type)} text-primary"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div>${activity.message}</div>
                        <small class="text-muted">${activity.time}</small>
                    </div>
                </div>
            `).join('');

            container.innerHTML = html;

        } catch (error) {
            console.error('Erro ao carregar atividade recente:', error);
        }
    }

    getActivityIcon(type) {
        const icons = {
            sale: 'shopping-cart',
            download: 'download',
            user: 'user-plus',
            product: 'film'
        };
        return icons[type] || 'info-circle';
    }

    async loadProducts() {
        try {
            const response = await fetch(`${this.apiBase}/products`);
            const data = await response.json();

            const tbody = document.getElementById('products-table');
            
            if (data.status === 'success' && data.products.length > 0) {
                const html = data.products.map(product => `
                    <tr>
                        <td>${product.id}</td>
                        <td>${product.name}</td>
                        <td>${product.price_stars} ⭐</td>
                        <td>0</td>
                        <td>
                            <span class="badge bg-${product.is_active ? 'success' : 'secondary'}">
                                ${product.is_active ? 'Ativo' : 'Inativo'}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary me-1" onclick="editProduct(${product.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteProduct(${product.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum produto encontrado</td></tr>';
            }

        } catch (error) {
            console.error('Erro ao carregar produtos:', error);
            this.showError('Erro ao carregar produtos');
        }
    }

    async loadSalesData() {
        try {
            const period = document.getElementById('sales-period')?.value || 7;
            
            // Simular dados de vendas
            document.getElementById('period-sales').textContent = '15';
            document.getElementById('period-revenue').textContent = '750';
            document.getElementById('avg-sale-value').textContent = '50';

            // Carregar tabela de transações
            const tbody = document.getElementById('sales-table');
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma transação encontrada</td></tr>';

        } catch (error) {
            console.error('Erro ao carregar dados de vendas:', error);
        }
    }

    async loadDownloads() {
        try {
            const response = await fetch(`${this.apiBase}/delivery/stats`);
            const data = await response.json();

            if (data.status === 'success') {
                document.getElementById('active-downloads').textContent = data.data.summary?.total_deliveries || 0;
                document.getElementById('total-downloads-count').textContent = data.data.summary?.total_downloads || 0;
            }

            // Carregar tabela de downloads
            const tbody = document.getElementById('downloads-table');
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum download encontrado</td></tr>';

        } catch (error) {
            console.error('Erro ao carregar downloads:', error);
        }
    }

    async loadUsers() {
        try {
            // Simular dados de usuários
            const tbody = document.getElementById('users-table');
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum usuário encontrado</td></tr>';

        } catch (error) {
            console.error('Erro ao carregar usuários:', error);
        }
    }

    async loadSettings() {
        try {
            // Carregar configurações atuais
            document.getElementById('download-expiry').value = '24';
            document.getElementById('max-downloads').value = '3';

        } catch (error) {
            console.error('Erro ao carregar configurações:', error);
        }
    }

    async addProduct() {
        try {
            const form = document.getElementById('add-product-form');
            const formData = new FormData();

            formData.append('name', document.getElementById('product-name').value);
            formData.append('price_stars', document.getElementById('product-price').value);
            formData.append('description', document.getElementById('product-description').value);
            
            const fileInput = document.getElementById('product-file');
            if (fileInput.files[0]) {
                formData.append('file', fileInput.files[0]);
            }

            const thumbnailInput = document.getElementById('product-thumbnail');
            if (thumbnailInput.files[0]) {
                formData.append('thumbnail', thumbnailInput.files[0]);
            }

            const response = await fetch(`${this.apiBase}/products`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess('Produto adicionado com sucesso!');
                bootstrap.Modal.getInstance(document.getElementById('addProductModal')).hide();
                form.reset();
                this.loadProducts();
            } else {
                this.showError(result.message || 'Erro ao adicionar produto');
            }

        } catch (error) {
            console.error('Erro ao adicionar produto:', error);
            this.showError('Erro ao adicionar produto');
        }
    }

    async cleanupExpiredDownloads() {
        try {
            const response = await fetch(`${this.apiBase}/delivery/cleanup`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess(result.message);
                this.loadDownloads();
            } else {
                this.showError('Erro na limpeza');
            }

        } catch (error) {
            console.error('Erro na limpeza:', error);
            this.showError('Erro na limpeza');
        }
    }

    async saveSettings() {
        try {
            const settings = {
                download_expiry: document.getElementById('download-expiry').value,
                max_downloads: document.getElementById('max-downloads').value,
                bot_token: document.getElementById('bot-token').value,
                webhook_url: document.getElementById('webhook-url').value
            };

            // Simular salvamento
            this.showSuccess('Configurações salvas com sucesso!');

        } catch (error) {
            console.error('Erro ao salvar configurações:', error);
            this.showError('Erro ao salvar configurações');
        }
    }

    searchUsers() {
        const query = document.getElementById('user-search').value;
        console.log('Buscando usuários:', query);
        // Implementar busca
    }

    refreshDashboard() {
        this.loadDashboard();
        this.showSuccess('Dashboard atualizado!');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'danger');
    }

    showToast(message, type = 'info') {
        // Criar toast notification
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        // Adicionar container de toasts se não existir
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        // Adicionar toast
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        toastContainer.appendChild(toastElement.firstElementChild);

        // Mostrar toast
        const toast = new bootstrap.Toast(toastContainer.lastElementChild);
        toast.show();

        // Remover após esconder
        toastContainer.lastElementChild.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toastContainer.lastElementChild);
        });
    }
}

// Funções globais para compatibilidade
function editProduct(id) {
    console.log('Editar produto:', id);
}

function deleteProduct(id) {
    if (confirm('Tem certeza que deseja excluir este produto?')) {
        console.log('Excluir produto:', id);
    }
}

function addProduct() {
    adminPanel.addProduct();
}

function cleanupExpiredDownloads() {
    adminPanel.cleanupExpiredDownloads();
}

function saveSettings() {
    adminPanel.saveSettings();
}

function searchUsers() {
    adminPanel.searchUsers();
}

function refreshDashboard() {
    adminPanel.refreshDashboard();
}

function loadSalesData() {
    adminPanel.loadSalesData();
}

// Inicializar painel admin quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
});

