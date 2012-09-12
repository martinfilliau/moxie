STATIC_DIR = moxie/core/static
PLACES_STATIC_DIR = moxie/places/static

MOXIE_JS_DIR = ${STATIC_DIR}/js/moxie
MOXIE_JS = ${STATIC_DIR}/js/moxie.js
MOXIE_JS_MIN = ${STATIC_DIR}/js/moxie.min.js

PLACES_JS = ${PLACES_STATIC_DIR}/js/moxie.places.js
PLACES_JS_MIN = ${PLACES_STATIC_DIR}/js/moxie.places.min.js
PLACES_HANDLEBARS_DIR = moxie/places/templates
PLACES_HANDLEBARS_JS = ${PLACES_STATIC_DIR}/js/moxie.places.templates.min.js

FOUNDATION_JS_DIR = ${STATIC_DIR}/js/foundation
FOUNDATION_JS = ${STATIC_DIR}/js/foundation.js
FOUNDATION_JS_MIN = ${STATIC_DIR}/js/foundation.min.js
MODERNIZR_JS_MIN = ${STATIC_DIR}/js/modernizr.min.js

build: static

static:
	@compass compile ${STATIC_DIR} -e production --force
	@cat ${FOUNDATION_JS_DIR}/jquery.js ${FOUNDATION_JS_DIR}/jquery.foundation.accordion.js ${FOUNDATION_JS_DIR}/jquery.foundation.alerts.js ${FOUNDATION_JS_DIR}/jquery.foundation.buttons.js ${FOUNDATION_JS_DIR}/jquery.foundation.forms.js ${FOUNDATION_JS_DIR}/jquery.foundation.mediaQueryToggle.js ${FOUNDATION_JS_DIR}/jquery.foundation.navigation.js ${FOUNDATION_JS_DIR}/jquery.foundation.orbit.js ${FOUNDATION_JS_DIR}/jquery.foundation.reveal.js ${FOUNDATION_JS_DIR}/jquery.foundation.tabs.js ${FOUNDATION_JS_DIR}/jquery.foundation.tooltips.js ${FOUNDATION_JS_DIR}/jquery.placeholder.js ${FOUNDATION_JS_DIR}/app.js > ${FOUNDATION_JS};
	@uglifyjs -nc ${FOUNDATION_JS} > ${FOUNDATION_JS_MIN};
	@uglifyjs -nc ${FOUNDATION_JS_DIR}/modernizr.foundation.js > ${MODERNIZR_JS_MIN};
	@cat ${MOXIE_JS_DIR}/handlebars.runtime.js > ${MOXIE_JS};
	@uglifyjs -nc ${MOXIE_JS} > ${MOXIE_JS_MIN};
	@uglifyjs -nc ${PLACES_JS} > ${PLACES_JS_MIN};
	@handlebars -m ${PLACES_HANDLEBARS_DIR} > ${PLACES_HANDLEBARS_JS};
	@echo "Static assets successfully built! - `date`";
