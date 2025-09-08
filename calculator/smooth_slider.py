from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def smooth_slider(label, id, value, min_val, max_val, step, is_currency=False, is_percentage=False, icon="", show_range=False):
    html = f"""
    <div class="card p-3 mb-3 bg-dark text-light rounded shadow-sm">
      <!-- Label and Value -->
      <div class="d-flex justify-content-between align-items-center mb-2">
        <label class="form-label mb-0 d-flex align-items-center gap-2">
          {f"<span>{icon}</span>" if icon else ""}
          {label}
        </label>
        <span id="{id}-display" class="fw-bold text-info">{value}</span>
      </div>

      <!-- Slider -->
      <input 
        type="range" 
        class="form-range" 
        id="{id}-slider" 
        min="{min_val}" 
        max="{max_val}" 
        step="{step}" 
        value="{value}"
        oninput="updateSliderValue('{id}', {str(is_currency).lower()}, {str(is_percentage).lower()})"
      >

      <!-- Min/Max Range -->
      {"<div class='d-flex justify-content-between text-muted small'><span>" + str(min_val) + "</span><span>" + str(max_val) + "</span></div>" if show_range else ""}

      <!-- Input Field -->
      <input 
        type="text" 
        id="{id}-input" 
        class="form-control form-control-sm mt-2 bg-dark text-light border-secondary"
        value="{value}"
        oninput="updateInputValue('{id}', {str(is_currency).lower()}, {str(is_percentage).lower()})"
      >
    </div>
    """
    return mark_safe(html)
