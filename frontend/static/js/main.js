// GoShala Care - Core Client Scripts
document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const toggleBtn = document.getElementById('mobileNavToggle');
    const sidebar = document.querySelector('.app-sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close sidebar if user clicks outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 900 && 
                !sidebar.contains(e.target) && 
                !toggleBtn.contains(e.target) && 
                sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    }

    // 2. Auto Dismiss Flash Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 6000);
    });

    // 3. Image Upload Instant Preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const previewContainer = document.getElementById(this.dataset.previewTarget || 'imagePreviewContainer');
            if (!previewContainer) return;

            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewContainer.innerHTML = `
                        <div style="position: relative; display: inline-block; margin-top: 14px;">
                            <img src="${e.target.result}" style="max-height: 220px; border-radius: 8px; border: 2px solid #1b4332; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                            <span style="display: block; font-size: 0.8rem; color: #526056; margin-top: 4px;">Ready for scan analysis</span>
                        </div>
                    `;
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // 4. Live Clinical Threshold Warning on Daily Vitals Form
    const tempInput = document.getElementById('temperatureInput');
    const tempNotice = document.getElementById('tempClinicalNotice');
    
    if (tempInput && tempNotice) {
        tempInput.addEventListener('input', () => {
            const val = parseFloat(tempInput.value);
            if (isNaN(val)) {
                tempNotice.innerHTML = '';
                return;
            }
            if (val > 40.2) {
                tempNotice.innerHTML = `<span style="color: #dc2626; font-weight: 600;"><i class="bi bi-exclamation-triangle-fill"></i> Critical Hyperthermia (${val}°C)! Indicates acute infection / sepsis.</span>`;
            } else if (val > 39.3) {
                tempNotice.innerHTML = `<span style="color: #d97706; font-weight: 600;"><i class="bi bi-thermometer-high"></i> Fever (${val}°C) - Normal cattle range is 38.0°C - 39.3°C.</span>`;
            } else if (val < 38.0) {
                tempNotice.innerHTML = `<span style="color: #d97706; font-weight: 600;"><i class="bi bi-thermometer-low"></i> Subnormal Temperature (${val}°C) - Watch for metabolic disorder/milk fever.</span>`;
            } else {
                tempNotice.innerHTML = `<span style="color: #059669; font-weight: 600;"><i class="bi bi-check-circle-fill"></i> Temperature is within healthy bovine range (38.0°C - 39.3°C).</span>`;
            }
        });
    }
});
