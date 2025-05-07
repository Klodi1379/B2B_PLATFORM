/**
 * Lidhje Biznesi - Main JavaScript
 * Version: 1.0.0
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize HTMX with boosted settings
    if (typeof htmx !== 'undefined') {
        htmx.config.useTemplateFragments = true;
        htmx.config.includeIndicatorStyles = false;
        htmx.config.allowEval = false;
        htmx.config.historyCacheSize = 10;
        
        // Add loading indicators for HTMX requests
        document.body.addEventListener('htmx:beforeRequest', function(event) {
            const target = event.detail.elt;
            // Add loading class to the element that triggered the request
            target.classList.add('htmx-loading');
            
            // If the target has a data-loading-target attribute, add loading class to that element
            const loadingTarget = target.getAttribute('data-loading-target');
            if (loadingTarget) {
                const loadingElement = document.querySelector(loadingTarget);
                if (loadingElement) {
                    loadingElement.classList.add('htmx-loading');
                }
            }
        });
        
        document.body.addEventListener('htmx:afterRequest', function(event) {
            const target = event.detail.elt;
            // Remove loading class from the element that triggered the request
            target.classList.remove('htmx-loading');
            
            // If the target has a data-loading-target attribute, remove loading class from that element
            const loadingTarget = target.getAttribute('data-loading-target');
            if (loadingTarget) {
                const loadingElement = document.querySelector(loadingTarget);
                if (loadingElement) {
                    loadingElement.classList.remove('htmx-loading');
                }
            }
        });
    }
    
    // General setup for Bootstrap components
    initializeTooltips();
    initializePopovers();
    setupDismissibleAlerts();
    
    // Setup for specific pages
    setupQuantityInputs();
    setupProductFilters();
    setupDeliveryStopSorting();
    setupNotificationPolling();
    
    // Setup for mobile responsive elements
    setupMobileNavigation();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Set up dismissible alerts to auto-dismiss after a delay
 */
function setupDismissibleAlerts() {
    var alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function(alert) {
        // Auto-dismiss success and info alerts after 5 seconds
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(function() {
                var closeButton = alert.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                }
            }, 5000);
        }
    });
}

/**
 * Set up quantity input controls (increment/decrement)
 */
function setupQuantityInputs() {
    document.addEventListener('click', function(event) {
        // Increment quantity
        if (event.target.classList.contains('btn-quantity-plus')) {
            var input = event.target.closest('.quantity-controls').querySelector('input');
            var step = parseFloat(input.getAttribute('step') || 1);
            var max = parseFloat(input.getAttribute('max') || Infinity);
            var newValue = parseFloat(input.value) + step;
            
            if (newValue <= max) {
                input.value = newValue;
                // Trigger change event
                var changeEvent = new Event('change', { bubbles: true });
                input.dispatchEvent(changeEvent);
            }
        }
        
        // Decrement quantity
        if (event.target.classList.contains('btn-quantity-minus')) {
            var input = event.target.closest('.quantity-controls').querySelector('input');
            var step = parseFloat(input.getAttribute('step') || 1);
            var min = parseFloat(input.getAttribute('min') || 0);
            var newValue = parseFloat(input.value) - step;
            
            if (newValue >= min) {
                input.value = newValue;
                // Trigger change event
                var changeEvent = new Event('change', { bubbles: true });
                input.dispatchEvent(changeEvent);
            }
        }
    });
}

/**
 * Setup product filter functionality for catalog pages
 */
function setupProductFilters() {
    const filterForm = document.getElementById('product-filter-form');
    if (!filterForm) return;
    
    // Handle filter form submission with HTMX if available
    filterForm.addEventListener('change', function(event) {
        if (typeof htmx !== 'undefined' && filterForm.getAttribute('hx-trigger') === 'change') {
            // HTMX will handle the form submission
            return;
        }
        
        // Otherwise, submit the form manually (with a small delay for multiple changes)
        if (filterForm.submitTimeout) {
            clearTimeout(filterForm.submitTimeout);
        }
        
        filterForm.submitTimeout = setTimeout(function() {
            filterForm.submit();
        }, 500);
    });
    
    // Handle category-supplier dependency
    const supplierSelect = document.getElementById('id_supplier');
    const categorySelect = document.getElementById('id_category');
    
    if (supplierSelect && categorySelect) {
        supplierSelect.addEventListener('change', function() {
            const supplierId = this.value;
            
            // If using HTMX, we can let it handle this
            if (typeof htmx !== 'undefined' && categorySelect.getAttribute('hx-trigger')) {
                return;
            }
            
            // Otherwise, make an AJAX request to update categories
            if (supplierId) {
                // Placeholder for AJAX call to update categories
                // In a real implementation, this would fetch categories for the selected supplier
                console.log('Would update categories for supplier ID:', supplierId);
            }
        });
    }
}

/**
 * Setup functionality for reordering delivery stops
 */
function setupDeliveryStopSorting() {
    const stopList = document.getElementById('delivery-stops-list');
    if (!stopList) return;
    
    // If using a drag-and-drop library, initialize it here
    
    // Update positions when form is submitted
    const deliveryForm = document.getElementById('delivery-plan-form');
    if (deliveryForm) {
        deliveryForm.addEventListener('submit', function(event) {
            // Update position values before submission
            const stopItems = stopList.querySelectorAll('.delivery-stop-item');
            stopItems.forEach(function(item, index) {
                const positionInput = item.querySelector('input.stop-position');
                if (positionInput) {
                    positionInput.value = index + 1;
                }
            });
        });
    }
}

/**
 * Setup polling for notifications
 */
function setupNotificationPolling() {
    const notificationCountElement = document.getElementById('notification-count');
    if (!notificationCountElement) return;
    
    // Poll for notifications every 60 seconds
    setInterval(function() {
        fetch('/notifications/api/count/')
            .then(response => response.json())
            .then(data => {
                if (data.count > 0) {
                    notificationCountElement.textContent = data.count;
                    notificationCountElement.style.display = 'inline-block';
                } else {
                    notificationCountElement.textContent = '0';
                    notificationCountElement.style.display = 'none';
                }
            })
            .catch(error => console.error('Error fetching notifications:', error));
    }, 60000);
}

/**
 * Setup mobile-specific navigation behavior
 */
function setupMobileNavigation() {
    // Close the mobile menu when a link is clicked
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        document.querySelectorAll('.navbar-nav .nav-link').forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            });
        });
    }
}

/**
 * Function to update category options when supplier changes
 * Used by product forms
 */
function updateCategoryOptions(supplierId) {
    const categorySelect = document.getElementById('id_category');
    if (!categorySelect) return;
    
    // Clear current options except the empty one
    while (categorySelect.options.length > 1) {
        categorySelect.remove(1);
    }
    
    if (!supplierId) return;
    
    // Fetch categories for this supplier
    fetch(`/products/api/categories/?supplier=${supplierId}`)
        .then(response => response.json())
        .then(data => {
            if (data.categories && data.categories.length > 0) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error fetching categories:', error));
}

/**
 * Function to update parent category options when supplier changes
 * Used by category forms
 */
function updateParentOptions(supplierId) {
    const parentSelect = document.getElementById('id_parent');
    if (!parentSelect) return;
    
    // Clear current options except the empty one
    while (parentSelect.options.length > 1) {
        parentSelect.remove(1);
    }
    
    if (!supplierId) return;
    
    // Fetch parent categories for this supplier
    fetch(`/products/api/categories/?supplier=${supplierId}&parent_only=true`)
        .then(response => response.json())
        .then(data => {
            if (data.categories && data.categories.length > 0) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    parentSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error fetching parent categories:', error));
}
