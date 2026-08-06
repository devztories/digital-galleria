document.addEventListener("DOMContentLoaded", function () {

    if (window.location.hash) {

        const section = document.querySelector(window.location.hash);

        if (section) {

            setTimeout(() => {

                section.scrollIntoView({
                    behavior: "smooth"
                });

            }, 100);

        }

    }

});