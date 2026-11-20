{# Pseudonymisation par hachage salé (SHA-256). Donnée pseudonymisée = toujours une donnée personnelle au sens RGPD. #}
{% macro pseudonymize(col) -%}
    sha256(concat('{{ var("pseudo_salt") }}', '|', cast({{ col }} as varchar)))
{%- endmacro %}
