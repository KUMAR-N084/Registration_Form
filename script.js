// Global variables
const form = document.getElementById('registrationForm');
const submitBtn = document.getElementById('submitBtn');
const photoInput = document.getElementById('photoInput');
const photoPreview = document.getElementById('photoPreview');
let uploadedPhotoData = '';
let isMinor = false;
let blockedField = null;

// Set max date for DOB to today
const today = new Date().toISOString().split('T')[0];
document.getElementById('dob').setAttribute('max', today);

const postalCodes = {
    '560001': { country: 'India', state: 'Karnataka', city: 'Bangalore' },
    '400001': { country: 'India', state: 'Maharashtra', city: 'Mumbai' },
    '90001': { country: 'USA', state: 'California', city: 'Los Angeles' }
};

// Dummy data blacklist - values that should be rejected
const dummyDataBlacklist = {
    emails: [
        'test@test.com', 'test@example.com', 'admin@admin.com', 'user@user.com',
        'demo@demo.com', 'demo@example.com', 'sample@sample.com', 'info@info.com',
        'test@gmail.com', 'dummy@dummy.com', 'temp@temp.com', 'hello@hello.com',
        'abc@abc.com', 'admin@example.com', 'test123@test.com', 'user123@user.com'
    ],
    usernames: [
        'test', 'admin', 'user', 'demo', 'sample', 'temp', 'hello', 'abc',
        'test123', 'user123', 'admin123', 'password', 'qwerty', 'asdfgh',
        'test1234', 'testuser', 'adminuser', 'demouser'
    ],
    names: [
        'test', 'admin', 'demo', 'sample', 'temp', 'dummy', 'abc', 'xyz', 'asdf'
    ],
    phones: [
        '1234567890', '9999999999', '1111111111', '5555555555', '0000000000',
        '6666666666', '7777777777', '8888888888', '1234567801', '9876543210'
    ]
};

// Function to detect repetitive patterns and gibberish
const hasRepetitivePattern = (str) => {
    // Don't check pure numeric strings (mobile numbers, postal codes, etc.)
    if (/^\d+$/.test(str)) {
        const firstChar = str[0];
        let consecutiveCount = 1;
        
        for (let i = 1; i < str.length; i++) {
            if (str[i] === firstChar) {
                consecutiveCount++;
            } else {
                break;
            }
        }
        
        if (consecutiveCount >= 8) return true;
        return false;
    }
    
    // Check for patterns like "adadada" or "asdasd" or "kukukuku"
    for (let len = 1; len <= Math.min(5, str.length / 2); len++) {
        const pattern = str.substring(0, len);
        let matchCount = 0;
        
        for (let i = 0; i < str.length; i += len) {
            const segment = str.substring(i, i + len);
            if (segment === pattern || (i + len > str.length && segment.startsWith(pattern))) {
                matchCount++;
            }
        }
        
        if (matchCount >= 3 && len <= 3) return true;
        if (matchCount >= 4 && len === 4) return true;
    }
    
    // Check for repeated 2-3 letter patterns
    for (let len = 2; len <= 4; len++) {
        for (let start = 0; start < str.length - (len * 2); start++) {
            const pattern = str.substring(start, start + len).toLowerCase();
            let repeatCount = 1;
            
            for (let i = start + len; i <= str.length - len; i += len) {
                const segment = str.substring(i, i + len).toLowerCase();
                if (segment === pattern) {
                    repeatCount++;
                } else {
                    break;
                }
            }
            
            if (repeatCount >= 3 && len <= 3) return true;
        }
    }
    
    // Check for consonant-heavy gibberish
    const consonants = (str.match(/[bcdfghjklmnpqrstvwxyz]/gi) || []).length;
    const vowels = (str.match(/[aeiou]/gi) || []).length;
    const total = consonants + vowels;
    
    if (total > 0 && str.length >= 8 && consonants / total > 0.75) {
        return true;
    }
    
    return false;
};

// Check repeated characters
const hasRepeat = (str, max = 3) => new RegExp(`(.)\\1{${max},}`).test(str);

// RFC 5322 compliant email validation
const isValidEmail = (email) => {
    const email_lower = email.toLowerCase();
    
    if (dummyDataBlacklist.emails.includes(email_lower)) {
        return false;
    }
    
    if (hasRepetitivePattern(email_lower)) {
        return false;
    }
    
    if (/\.(com|net|org|edu|gov|co|in|uk|us|au|de|fr|it|es|br|ca|mx|ru|cn|jp|ind){2,}$/.test(email_lower)) {
        return false;
    }
    
    if (email.length > 320) return false;
    
    const [localPart, ...domainParts] = email.split('@');
    const domain = domainParts.join('@');
    
    if (domainParts.length !== 1) return false;
    
    if (!localPart || localPart.length > 64) return false;
    if (localPart.startsWith('.') || localPart.endsWith('.')) return false;
    if (localPart.includes('..')) return false;
    
    if (!/^[A-Za-z0-9._+%-]+$/.test(localPart)) return false;
    
    if (!/[A-Za-z]/.test(localPart)) return false;
    
    if (!domain || domain.length > 255) return false;
    if (domain.startsWith('-') || domain.endsWith('-')) return false;
    if (domain.startsWith('.') || domain.endsWith('.')) return false;
    if (domain.includes('..')) return false;
    
    const labels = domain.split('.');
    
    if (labels.length < 2) return false;
    
    const tld = labels[labels.length - 1];
    if (!/^[A-Za-z]{2,6}$/.test(tld)) return false;
    
    for (let label of labels) {
        if (!label || label.length > 63) return false;
        if (label.startsWith('-') || label.endsWith('-')) return false;
        if (!/^[A-Za-z0-9-]+$/.test(label)) return false;
        
        if (!/[A-Za-z]/.test(label)) return false;
    }
    
    return true;
};

// Enhanced name validation
const isValidName = (str) => {
    if (!str || str.length > 50) return false;
    
    if (dummyDataBlacklist.names.includes(str.toLowerCase())) return false;
    
    if (hasRepetitivePattern(str)) return false;
    
    if (/^\.?[A-Za-z]\.?$/.test(str)) return true;
    
    if (!/^[A-Za-z]+(?:[.\s'-]*[A-Za-z]+)*\.?$/.test(str)) return false;
    
    if (/\s{2,}/.test(str)) return false;
    
    if (str !== str.trim()) return false;
    
    return true;
};

// Validation rules
const rules = {
    name: { 
        pattern: /^[A-Za-z]+(?:[.\s'-]*[A-Za-z]+)*\.?$/, 
        msg: 'Letters, spaces, dots, apostrophes. No repeated patterns',
        customValidator: isValidName
    },
    username: { 
        pattern: /^[A-Za-z0-9_@.#$%&*+-]{3,}$/, 
        msg: 'Letters/numbers/special chars, min 3. No dummy/repeated patterns',
        customValidator: (val) => {
            if (dummyDataBlacklist.usernames.includes(val.toLowerCase())) return false;
            if (hasRepetitivePattern(val)) return false;
            return true;
        }
    },
    email: { 
        pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, 
        msg: 'Valid email required',
        customValidator: isValidEmail
    },
    mobile: { 
        pattern: /^[6789][0-9]{9}$/, 
        msg: 'Exactly 10 digits starting with 6, 7, 8, or 9',
        customValidator: (val) => {
            if (dummyDataBlacklist.phones.includes(val)) return false;
            if (hasRepetitivePattern(val)) return false;
            return true;
        }
    },
    password: { 
        pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/, 
        msg: 'Min 8: A-Z, a-z, 0-9, special. No repeated patterns',
        customValidator: (val) => {
            if (hasRepetitivePattern(val)) return false;
            return true;
        }
    },
    address: { 
        pattern: /^[A-Za-z0-9\s.,#-]{10,}$/, 
        msg: 'Min 10 chars. No repeated patterns',
        customValidator: (val) => {
            if (hasRepetitivePattern(val)) return false;
            return true;
        }
    },
    postal: { 
        pattern: /^[0-9]{6}$/, 
        msg: 'Must be exactly 6 digits',
        customValidator: (val) => {
            if (hasRepetitivePattern(val)) return false;
            return true;
        }
    },
    securityAnswer: { 
        pattern: /^.{2,}$/, 
        msg: 'Min 2 characters. No repeated patterns',
        customValidator: (val) => {
            if (hasRepetitivePattern(val)) return false;
            return true;
        }
    },
    required: { pattern: /^.+$/, msg: 'Required' }
};

const filters = {
    name: v => {
        v = v.replace(/[^A-Za-z\s.'-]/g, '');
        
        if (/^\.?[A-Za-z]\.?$/.test(v)) {
            v = v.replace(/[a-z]/g, c => c.toUpperCase());
        } else {
            v = v.replace(/^[a-z]/, c => c.toUpperCase());
            v = v.replace(/\s[a-z]/g, c => c.toUpperCase());
            v = v.replace(/\.[a-z]/g, c => c.toUpperCase());
            v = v.replace(/-[a-z]/g, c => c.toUpperCase());
            v = v.replace(/'[a-z]/g, c => c.toUpperCase());
        }
        return v;
    },
    username: v => v.replace(/[^A-Za-z0-9_@.#$%&*+-]/g, ''),
    mobile: v => v.replace(/[^0-9]/g, ''),
    address: v => v.replace(/[^A-Za-z0-9\s.,#-]/g, ''),
    postal: v => v.replace(/[^0-9]/g, '')
};

// Add DOB input validation
document.getElementById('dob').addEventListener('change', function() {
    validate(this, true);
});

// Block/unblock field navigation
const blockField = f => { blockedField = f; f.style.outline = '3px solid #e74c3c'; };
const unblockField = f => { if (blockedField === f) { blockedField = null; f.style.outline = ''; } };

document.addEventListener('focusin', e => {
    if (blockedField && e.target !== blockedField && e.target.tagName !== 'BODY') {
        e.preventDefault();
        e.stopPropagation();
        blockedField.focus();
        blockedField.classList.add('invalid');
    }
}, true);

// Validation function
const validate = (field, shouldLog = false) => {
    const rule = field.dataset.rule;
    const val = field.value.trim();
    const err = field.parentElement.querySelector('.error-message') || document.getElementById(field.id + 'Error');
    if (!err) return true;

    let valid = false, msg = '';

    // Check for repetitive patterns in all fields FIRST
    if (val && ['name', 'username', 'mobile', 'address', 'securityAnswer', 'email', 'password', 'postal'].includes(rule)) {
        if (hasRepetitivePattern(val)) {
            msg = 'No gibberish or repetitive patterns allowed';
            field.setAttribute('aria-invalid', true);
            field.className = field.className.replace(/\b(valid|invalid)\b/g, '') + ' invalid';
            if (field.parentElement?.classList.contains('form-group')) {
                field.parentElement.classList.toggle('valid', false);
            }
            err.textContent = msg;
            checkFormValid();
            return false;
        }
    }

    if (field.id === 'confirmPassword') {
        valid = val === document.getElementById('password').value && val;
        msg = valid ? '' : 'Passwords do not match';
    } else if (field.id === 'dob') {
        if (!val) { 
            msg = 'Date of birth required';
            const ageContainer = document.getElementById('ageDisplayContainer');
            if (ageContainer) ageContainer.style.display = 'none';
        }
        else {
            const inputDate = new Date(val);
            const today = new Date();
            
            if (inputDate > today) {
                msg = 'Date cannot be in the future';
                valid = false;
            } else {
                const age = Math.floor((Date.now() - inputDate.getTime()) / 31557600000);
                
                const year = inputDate.getFullYear();
                const currentYear = today.getFullYear();
                
                if (year < 1900 || year > currentYear) {
                    msg = 'Year must be between 1900 and ' + currentYear;
                    valid = false;
                } else {
                    valid = age >= 13;
                    msg = valid ? '' : 'Must be 13+ years old';
                }
                
                const ageContainer = document.getElementById('ageDisplayContainer');
                const ageDisplay = document.getElementById('ageDisplay');
                if (ageContainer && ageDisplay && valid) {
                    ageDisplay.textContent = age;
                    ageContainer.style.display = 'block';
                } else if (ageContainer) {
                    ageContainer.style.display = 'none';
                }
                
                const consentSection = document.getElementById('parentalConsentSection');
                if (valid && age >= 13 && age < 18) {
                    consentSection.classList.remove('hidden');
                    isMinor = true;
                } else {
                    consentSection.classList.add('hidden');
                    isMinor = false;
                }
            }
        }
    } else if (rules[rule]) {
        valid = rules[rule].pattern.test(val);
        
        if (valid && rules[rule].customValidator) {
            valid = rules[rule].customValidator(val);
        }
        
        msg = valid ? '' : rules[rule].msg;
    } else {
        valid = val.length > 0;
        msg = valid ? '' : 'Required';
    }

    field.setAttribute('aria-invalid', !valid);
    field.className = field.className.replace(/\b(valid|invalid)\b/g, '') + (valid ? ' valid' : ' invalid');
    if (field.parentElement?.classList.contains('form-group')) {
        field.parentElement.classList.toggle('valid', valid);
    }
    err.textContent = msg;
    if (valid) {
        unblockField(field);
        if (shouldLog) console.log(`✅ ${field.id} is correct`);
    }
    checkFormValid();
    return valid;
};

// Apply filters and validation
document.querySelectorAll('[data-rule]').forEach(f => {
    const rule = f.dataset.rule;
    if (filters[rule]) {
        f.addEventListener('input', e => {
            e.target.value = filters[rule](e.target.value);
            validate(f);
        });
    } else {
        f.addEventListener('input', () => validate(f));
    }
    
    f.addEventListener('blur', async () => { 
        const localValid = validate(f, true);
        if (f.value.trim()) {
            try {
                const payload = { "field": f.id, "value": f.value.trim() };
                if (f.id === 'confirmPassword') {
                    payload.passwordValue = document.getElementById('password').value;
                }
                
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                const err = f.parentElement.querySelector('.error-message') || document.getElementById(f.id + 'Error');
                
                if (err) {
                    err.textContent = result.message;
                    err.style.color = result.valid ? '#00E676' : '#FF5252';
                    if (result.valid) console.log(`✅ ${f.id}: ${result.message}`);
                    setTimeout(() => err.style.color = '#FF5252', 3000);
                }
                
            } catch (error) {
                console.error('Validation error:', error);
            }
        }
        if (!localValid && f.value.trim()) blockField(f); 
    });
    f.addEventListener('keydown', e => {
        if (e.key === 'Enter' && f.tagName !== 'TEXTAREA') {
            e.preventDefault();
            validate(f, true) ? (unblockField(f), focusNext(f)) : blockField(f);
        }
    });
});

const focusNext = cur => {
    const all = Array.from(document.querySelectorAll('input:not([hidden]):not([disabled]), textarea:not([disabled]), select:not([disabled]), button'));
    const idx = all.indexOf(cur);
    if (idx < all.length - 1) all[idx + 1].focus();
};

// Gender & Terms validation
document.querySelectorAll('[name="gender"]').forEach(r => r.addEventListener('change', function() {
    document.getElementById('genderError').textContent = '';
    this.setAttribute('aria-checked', 'true');
    console.log(`✅ Gender selected: ${this.value}`);
    checkFormValid();
}));

document.getElementById('terms').addEventListener('change', function() {
    document.getElementById('termsError').textContent = this.checked ? '' : 'Must agree';
    if (this.checked) console.log('✅ Terms agreed');
    checkFormValid();
});

const guardianConsentEl = document.getElementById('guardianConsent');
if (guardianConsentEl) {
    guardianConsentEl.addEventListener('change', function() {
        document.getElementById('guardianConsentError').textContent = this.checked ? '' : 'Consent required';
        if (this.checked) console.log('✅ Guardian consent granted');
        checkFormValid();
    });
}

// Photo upload with validation
if (photoInput) {
    photoInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const err = document.getElementById('photoError');
        const prev = photoPreview;
        
        err.textContent = '';
        prev.classList.remove('error');
        
        if (!file) return err.textContent = 'Photo required', uploadedPhotoData = '', prev.classList.add('error'), checkFormValid();
        
        const valid = ['.jpg', '.jpeg', '.png', '.svg'].some(ext => file.name.toLowerCase().endsWith(ext)) &&
                      ['image/jpeg', 'image/jpg', 'image/png', 'image/svg+xml'].includes(file.type);
        
        if (!valid) return err.textContent = '❌ Only JPG, PNG, SVG allowed', this.value = '', prev.classList.add('error'), checkFormValid();
        if (file.size > 5242880) return err.textContent = `❌ Too large (${(file.size/1048576).toFixed(2)}MB). Max 5MB`, this.value = '', prev.classList.add('error'), checkFormValid();
        if (file.size < 1024) return err.textContent = '❌ File too small', this.value = '', prev.classList.add('error'), checkFormValid();
        
        const reader = new FileReader();
        reader.onerror = () => (err.textContent = '❌ Error reading file', this.value = '', prev.classList.add('error'), checkFormValid());
        reader.onload = e => {
            const img = new Image();
            img.onerror = () => (err.textContent = '❌ Invalid image', this.value = '', prev.classList.add('error'), checkFormValid());
            img.onload = () => {
                if (img.width < 100 || img.height < 100) return err.textContent = '❌ Min 100x100px', this.value = '', prev.classList.add('error'), checkFormValid();
                if (img.width > 5000 || img.height > 5000) return err.textContent = '❌ Max 5000x5000px', this.value = '', prev.classList.add('error'), checkFormValid();
                
                uploadedPhotoData = e.target.result;
                prev.innerHTML = `<img src="${uploadedPhotoData}" loading="lazy" alt="Profile">`;
                prev.classList.add('has-image');
                err.style.color = '#27ae60';
                err.textContent = `✓ Uploaded (${(file.size/1024).toFixed(1)}KB, ${img.width}x${img.height}px)`;
                console.log('✅ Photo uploaded successfully');
                setTimeout(() => (err.textContent = '', err.style.color = '#e74c3c'), 3000);
                checkFormValid();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

// Password toggle
document.querySelectorAll('.toggle-password').forEach(icon => {
    const toggle = function() {
        const inp = this.previousElementSibling;
        inp.type = inp.type === 'password' ? 'text' : 'password';
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    };
    icon.addEventListener('click', toggle);
    icon.addEventListener('keydown', e => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), toggle.call(icon)));
});

// Check form validity
let validityTimeout;
const checkFormValid = () => {
    if (!submitBtn) return;
    clearTimeout(validityTimeout);
    validityTimeout = setTimeout(() => {
        const fields = ['firstName', 'lastName', 'username', 'email', 'mobile', 'dob', 'postalCode', 'country', 'state', 'city', 'education', 'password', 'confirmPassword', 'address', 'securityQuestion', 'securityAnswer'];
        const valid = fields.every(id => document.getElementById(id)?.classList.contains('valid'));
        const checks = [
            document.querySelector('[name="gender"]:checked'),
            document.getElementById('terms').checked,
            uploadedPhotoData,
            !isMinor || (['guardianName', 'guardianEmail', 'guardianPhone'].every(id => document.getElementById(id)?.classList.contains('valid')) && document.getElementById('guardianConsent')?.checked)
        ];
        submitBtn.disabled = !(valid && checks.every(Boolean));
    }, 50);
};

// Form submission with API call
if (form) {
    form.addEventListener('submit', async e => {
        e.preventDefault();
        
        console.log('🚀 Form submission started...');
        
        // Prepare display data for modal
        const displayData = {
            'First Name': document.getElementById('firstName').value,
            'Last Name': document.getElementById('lastName').value,
            'Username': document.getElementById('username').value,
            'Email': document.getElementById('email').value,
            'Mobile': document.getElementById('mobile').value,
            'Date of Birth': document.getElementById('dob').value,
            'Gender': document.querySelector('[name="gender"]:checked').value,
            'Postal Code': document.getElementById('postalCode').value,
            'Country': document.getElementById('country').value,
            'State': document.getElementById('state').value,
            'City': document.getElementById('city').value,
            'Education': document.getElementById('education').value,
            'Address': document.getElementById('address').value,
            'Security Question': document.getElementById('securityQuestion').selectedOptions[0].text,
            'Security Answer': document.getElementById('securityAnswer').value
        };
        
        if (isMinor) {
            displayData['Guardian Name'] = document.getElementById('guardianName').value;
            displayData['Guardian Email'] = document.getElementById('guardianEmail').value;
            displayData['Guardian Phone'] = document.getElementById('guardianPhone').value;
        }
        
        // Prepare API data for server
        const securityQuestionSelect = document.getElementById('securityQuestion');
        const securityQuestionText = securityQuestionSelect.options[securityQuestionSelect.selectedIndex].text;
        
        const apiData = {
            firstName: document.getElementById('firstName').value,
            lastName: document.getElementById('lastName').value,
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            mobile: document.getElementById('mobile').value,
            dob: document.getElementById('dob').value,
            gender: document.querySelector('[name="gender"]:checked').value,
            postalCode: document.getElementById('postalCode').value,
            country: document.getElementById('country').value,
            state: document.getElementById('state').value,
            city: document.getElementById('city').value,
            education: document.getElementById('education').value,
            address: document.getElementById('address').value,
            securityQuestion: securityQuestionText,
            securityAnswer: document.getElementById('securityAnswer').value,
            password: document.getElementById('password').value,
            profilePhoto: uploadedPhotoData
        };
        
        if (isMinor) {
            apiData.guardianName = document.getElementById('guardianName').value;
            apiData.guardianEmail = document.getElementById('guardianEmail').value;
            apiData.guardianPhone = document.getElementById('guardianPhone').value;
        }
        
        console.log('📦 Sending data:', apiData);
        
        // Show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        }
        
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiData)
            });
            
            console.log('📡 Response status:', response.status);
            
            const result = await response.json();
            console.log('✅ Response data:', result);
            
            if (result.success) {
                // Show success modal
                document.getElementById('modalPhoto').innerHTML = `<img src="${uploadedPhotoData}" loading="lazy" alt="Profile">`;
                document.getElementById('confirmTable').innerHTML = '<tr><th>Field</th><th>Value</th></tr>' + 
                    Object.entries(displayData).map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join('');
                document.getElementById('confirmModal').classList.add('show');
                document.getElementById('closeModal').focus();
                
                console.log('✅ Registration successful!');
            } else {
                console.error('❌ Server error:', result.message);
                alert('Error: ' + result.message);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Register';
                }
            }
        } catch (error) {
            console.error('❌ Network error:', error);
            alert('Registration failed. Please check console for details.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Register';
            }
        }
    });
}

// Reset form
const reset = () => {
    document.getElementById('confirmModal').classList.remove('show');
    if (form) form.reset();
    if (photoPreview) {
        photoPreview.innerHTML = '<i class="fas fa-user-circle"></i><span>Click to Upload</span>';
        photoPreview.className = 'photo-preview';
    }
    uploadedPhotoData = '';
    document.querySelectorAll('.valid, .invalid').forEach(el => el.classList.remove('valid', 'invalid'));
    document.querySelectorAll('.error-message').forEach(el => (el.textContent = '', el.style.color = '#e74c3c'));
    document.getElementById('parentalConsentSection').classList.add('hidden');
    document.getElementById('ageDisplayContainer').style.display = 'none';
    ['state', 'city'].forEach(id => {
        const el = document.getElementById(id);
        el.disabled = true;
        el.innerHTML = `<option value="">Select ${id.charAt(0).toUpperCase() + id.slice(1)}</option>`;
    });
    isMinor = false;
    blockedField = null;
    checkFormValid();
    document.getElementById('firstName').focus();
};

const closeModalEl = document.getElementById('closeModal');
if(closeModalEl) {
    closeModalEl.addEventListener('click', reset);
    closeModalEl.addEventListener('keydown', e => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), reset()));
}
const confirmModalEl = document.getElementById('confirmModal');
if (confirmModalEl) {
    confirmModalEl.addEventListener('keydown', e => e.key === 'Escape' && reset());
}

// Social buttons
document.querySelectorAll('.social-btn').forEach(btn => btn.addEventListener('click', () => alert(`${btn.classList.contains('google') ? 'Google' : btn.classList.contains('facebook') ? 'Facebook' : 'X'} login coming soon!`)));

// Photo preview click
const photoUploadBtn = document.querySelector('.photo-upload-btn');
if (photoUploadBtn && photoInput) {
    photoUploadBtn.addEventListener('keydown', e => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), photoInput.click()));
}

// Load Countries
document.addEventListener('DOMContentLoaded', async () => {
    const countrySelect = document.getElementById('country');
    
    try {
        const response = await fetch('/api/countries');
        const countries = await response.json();
        
        if (Array.isArray(countries)) {
            countries.forEach(country => {
                countrySelect.add(new Option(country.name, country.id));
            });
        }
    } catch (error) {
        console.error('Error loading countries:', error);
    }
});

// Country Change Listener
document.getElementById('country').addEventListener('change', async function() {
    const stateSelect = document.getElementById('state');
    const citySelect = document.getElementById('city');
    const countryId = this.value;
    
    stateSelect.innerHTML = '<option value="">Select State</option>';
    citySelect.innerHTML = '<option value="">Select City</option>';
    stateSelect.disabled = true;
    citySelect.disabled = true;
    
    validate(this, true);

    if (countryId) {
        stateSelect.innerHTML = '<option value="">Loading...</option>';
        try {
            const response = await fetch(`/api/states/${countryId}`);
            const states = await response.json();
            
            stateSelect.innerHTML = '<option value="">Select State</option>';
            if (Array.isArray(states) && states.length > 0) {
                states.forEach(state => {
                    stateSelect.add(new Option(state.name, state.id));
                });
                stateSelect.disabled = false;
            } else {
                 stateSelect.innerHTML = '<option value="">No states found</option>';
            }
        } catch (error) {
            console.error('Error loading states:', error);
            stateSelect.innerHTML = '<option value="">Error loading states</option>';
        }
    }
});

// State Change Listener
document.getElementById('state').addEventListener('change', async function() {
    const citySelect = document.getElementById('city');
    const countryId = document.getElementById('country').value;
    const stateId = this.value;
    
    citySelect.innerHTML = '<option value="">Select City</option>';
    citySelect.disabled = true;
    
    validate(this, true);

    if (countryId && stateId) {
        citySelect.innerHTML = '<option value="">Loading...</option>';
        try {
            const response = await fetch(`/api/cities/${countryId}/${stateId}`);
            const cities = await response.json();
            
            citySelect.innerHTML = '<option value="">Select City</option>';
            if (Array.isArray(cities) && cities.length > 0) {
                cities.forEach(city => {
                    citySelect.add(new Option(city.name, city.name));
                });
                citySelect.disabled = false;
            } else {
                citySelect.innerHTML = '<option value="">No cities found</option>';
            }
        } catch (error) {
            console.error('Error loading cities:', error);
            citySelect.innerHTML = '<option value="">Error loading cities</option>';
        }
    }
});

// City Change Listener
document.getElementById('city').addEventListener('change', function() {
    validate(this, true);
});

// Initialize
document.getElementById('firstName').focus();