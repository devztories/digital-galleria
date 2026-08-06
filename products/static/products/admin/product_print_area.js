document.addEventListener(
    "DOMContentLoaded",
    function () {

        // =================================================
        // GET DJANGO ADMIN FIELDS
        // =================================================

        const imageInput =
            document.getElementById(
                "id_image"
            );

        const customizableInput =
            document.getElementById(
                "id_is_customizable"
            );

        const xInput =
            document.getElementById(
                "id_customization_x"
            );

        const yInput =
            document.getElementById(
                "id_customization_y"
            );

        const widthInput =
            document.getElementById(
                "id_customization_width"
            );

        const heightInput =
            document.getElementById(
                "id_customization_height"
            );


        // =================================================
        // STOP IF FIELDS DON'T EXIST
        // =================================================

        if (

            !xInput ||

            !yInput ||

            !widthInput ||

            !heightInput

        ) {

            return;

        }


        // =================================================
        // CREATE VISUAL EDITOR
        // =================================================

        const editor = document.createElement(
            "div"
        );

        editor.className =
            "print-area-admin-editor";


        editor.innerHTML = `

            <div class="print-editor-header">

                <h2>
                    Visual Print Area Editor
                </h2>

                <p>
                    Drag the rectangle to move the
                    printable area.

                    Drag the corner handle to resize it.
                </p>

            </div>


            <div
                class="print-editor-stage"
                id="printEditorStage"
            >

                <img
                    id="printEditorImage"
                    class="print-editor-image"
                    alt="Product preview"
                >


                <div
                    id="printAreaBox"
                    class="print-area-box"
                >

                    <span
                        class="print-area-label"
                    >
                        PRINT AREA
                    </span>


                    <div
                        id="printResizeHandle"
                        class="print-resize-handle"
                    ></div>

                </div>

            </div>


            <div class="print-editor-values">

                <div>

                    <strong>X</strong>

                    <span id="printValueX">
                        0
                    </span>%

                </div>


                <div>

                    <strong>Y</strong>

                    <span id="printValueY">
                        0
                    </span>%

                </div>


                <div>

                    <strong>Width</strong>

                    <span id="printValueWidth">
                        0
                    </span>%

                </div>


                <div>

                    <strong>Height</strong>

                    <span id="printValueHeight">
                        0
                    </span>%

                </div>

            </div>


            <div class="print-editor-actions">

                <button
                    type="button"
                    id="printCenterButton"
                    class="button"
                >
                    Center Print Area
                </button>


                <button
                    type="button"
                    id="printResetButton"
                    class="button"
                >
                    Reset
                </button>

            </div>

        `;


        // =================================================
        // INSERT EDITOR
        //
        // Put editor after customization height row.
        // =================================================

        const heightRow =
            heightInput.closest(
                ".form-row"
            );


        if (heightRow) {

            heightRow.insertAdjacentElement(

                "afterend",

                editor

            );

        }

        else {

            heightInput.parentElement
                .appendChild(
                    editor
                );

        }


        // =================================================
        // GET EDITOR ELEMENTS
        // =================================================

        const stage =
            document.getElementById(
                "printEditorStage"
            );

        const previewImage =
            document.getElementById(
                "printEditorImage"
            );

        const printBox =
            document.getElementById(
                "printAreaBox"
            );

        const resizeHandle =
            document.getElementById(
                "printResizeHandle"
            );

        const valueX =
            document.getElementById(
                "printValueX"
            );

        const valueY =
            document.getElementById(
                "printValueY"
            );

        const valueWidth =
            document.getElementById(
                "printValueWidth"
            );

        const valueHeight =
            document.getElementById(
                "printValueHeight"
            );

        const centerButton =
            document.getElementById(
                "printCenterButton"
            );

        const resetButton =
            document.getElementById(
                "printResetButton"
            );


        // =================================================
        // STATE
        // =================================================

        let dragging = false;

        let resizing = false;

        let startMouseX = 0;

        let startMouseY = 0;

        let startX = 0;

        let startY = 0;

        let startWidth = 0;

        let startHeight = 0;


        // =================================================
        // HELPER
        // =================================================

        function clamp(
            value,
            minimum,
            maximum
        ) {

            return Math.min(

                Math.max(
                    value,
                    minimum
                ),

                maximum

            );

        }


        // =================================================
        // GET NUMBER
        // =================================================

        function numberValue(
            input,
            fallback
        ) {

            const value =
                parseFloat(
                    input.value
                );


            if (
                Number.isNaN(
                    value
                )
            ) {

                return fallback;

            }


            return value;

        }


        // =================================================
        // UPDATE BOX FROM INPUT FIELDS
        // =================================================

        function updateBoxFromFields() {

            let x =
                numberValue(
                    xInput,
                    25
                );

            let y =
                numberValue(
                    yInput,
                    25
                );

            let width =
                numberValue(
                    widthInput,
                    50
                );

            let height =
                numberValue(
                    heightInput,
                    50
                );


            // ---------------------------------------------
            // VALIDATE
            // ---------------------------------------------

            x = clamp(
                x,
                0,
                99
            );

            y = clamp(
                y,
                0,
                99
            );


            width = clamp(

                width,

                1,

                100 - x

            );


            height = clamp(

                height,

                1,

                100 - y

            );


            // ---------------------------------------------
            // UPDATE VISUAL BOX
            // ---------------------------------------------

            printBox.style.left =
                x + "%";

            printBox.style.top =
                y + "%";

            printBox.style.width =
                width + "%";

            printBox.style.height =
                height + "%";


            updateValueLabels();

        }


        // =================================================
        // UPDATE VALUE LABELS
        // =================================================

        function updateValueLabels() {

            valueX.textContent =

                Number(
                    xInput.value || 0
                )
                .toFixed(2);


            valueY.textContent =

                Number(
                    yInput.value || 0
                )
                .toFixed(2);


            valueWidth.textContent =

                Number(
                    widthInput.value || 0
                )
                .toFixed(2);


            valueHeight.textContent =

                Number(
                    heightInput.value || 0
                )
                .toFixed(2);

        }


        // =================================================
        // UPDATE DJANGO INPUTS FROM VISUAL BOX
        // =================================================

        function updateFieldsFromBox() {

            const stageWidth =
                stage.clientWidth;

            const stageHeight =
                stage.clientHeight;


            if (

                stageWidth <= 0 ||

                stageHeight <= 0

            ) {

                return;

            }


            const x =

                (
                    printBox.offsetLeft
                    /
                    stageWidth
                )

                *

                100;


            const y =

                (
                    printBox.offsetTop
                    /
                    stageHeight
                )

                *

                100;


            const width =

                (
                    printBox.offsetWidth
                    /
                    stageWidth
                )

                *

                100;


            const height =

                (
                    printBox.offsetHeight
                    /
                    stageHeight
                )

                *

                100;


            xInput.value =
                x.toFixed(2);

            yInput.value =
                y.toFixed(2);

            widthInput.value =
                width.toFixed(2);

            heightInput.value =
                height.toFixed(2);


            updateValueLabels();

        }


        // =================================================
        // EXISTING PRODUCT IMAGE
        //
        // Django Admin ImageField usually shows:
        //
        // Currently: /media/products/...
        // =================================================

        function loadExistingImage() {

            if (!imageInput) {

                return;

            }


            const imageRow =
                imageInput.closest(
                    ".form-row"
                );


            if (!imageRow) {

                return;

            }


            const links =
                imageRow.querySelectorAll(
                    "a"
                );


            for (
                const link of links
            ) {

                const href =
                    link.getAttribute(
                        "href"
                    );


                if (

                    href &&

                    (
                        href.includes(
                            "/media/"
                        )

                        ||

                        /\.(jpg|jpeg|png|webp)$/i
                            .test(
                                href
                            )
                    )

                ) {

                    previewImage.src =
                        href;

                    return;

                }

            }

        }


        // =================================================
        // NEW IMAGE SELECTED
        // =================================================

        if (imageInput) {

            imageInput.addEventListener(

                "change",

                function () {

                    const file =
                        this.files[0];


                    if (!file) {

                        return;

                    }


                    if (

                        !file.type.startsWith(
                            "image/"
                        )

                    ) {

                        return;

                    }


                    const reader =
                        new FileReader();


                    reader.onload =
                        function (
                            event
                        ) {

                            previewImage.src =

                                event.target.result;

                        };


                    reader.readAsDataURL(
                        file
                    );

                }

            );

        }


        // =================================================
        // DRAG PRINT AREA
        // =================================================

        printBox.addEventListener(

            "pointerdown",

            function (
                event
            ) {

                // -----------------------------------------
                // RESIZE HANDLE IS SEPARATE
                // -----------------------------------------

                if (

                    event.target ===
                    resizeHandle

                ) {

                    return;

                }


                event.preventDefault();


                dragging = true;


                startMouseX =
                    event.clientX;

                startMouseY =
                    event.clientY;


                startX =
                    printBox.offsetLeft;

                startY =
                    printBox.offsetTop;


                printBox.setPointerCapture(
                    event.pointerId
                );

            }

        );


        // =================================================
        // START RESIZE
        // =================================================

        resizeHandle.addEventListener(

            "pointerdown",

            function (
                event
            ) {

                event.preventDefault();

                event.stopPropagation();


                resizing = true;


                startMouseX =
                    event.clientX;

                startMouseY =
                    event.clientY;


                startWidth =
                    printBox.offsetWidth;

                startHeight =
                    printBox.offsetHeight;


                resizeHandle.setPointerCapture(
                    event.pointerId
                );

            }

        );


        // =================================================
        // POINTER MOVE
        // =================================================

        document.addEventListener(

            "pointermove",

            function (
                event
            ) {

                // =========================================
                // DRAGGING
                // =========================================

                if (dragging) {

                    const deltaX =

                        event.clientX

                        -

                        startMouseX;


                    const deltaY =

                        event.clientY

                        -

                        startMouseY;


                    let newX =

                        startX

                        +

                        deltaX;


                    let newY =

                        startY

                        +

                        deltaY;


                    const maxX =

                        stage.clientWidth

                        -

                        printBox.offsetWidth;


                    const maxY =

                        stage.clientHeight

                        -

                        printBox.offsetHeight;


                    newX = clamp(

                        newX,

                        0,

                        maxX

                    );


                    newY = clamp(

                        newY,

                        0,

                        maxY

                    );


                    printBox.style.left =

                        newX + "px";


                    printBox.style.top =

                        newY + "px";


                    updateFieldsFromBox();

                }


                // =========================================
                // RESIZING
                // =========================================

                if (resizing) {

                    const deltaX =

                        event.clientX

                        -

                        startMouseX;


                    const deltaY =

                        event.clientY

                        -

                        startMouseY;


                    let newWidth =

                        startWidth

                        +

                        deltaX;


                    let newHeight =

                        startHeight

                        +

                        deltaY;


                    const minimumSize =
                        30;


                    const maximumWidth =

                        stage.clientWidth

                        -

                        printBox.offsetLeft;


                    const maximumHeight =

                        stage.clientHeight

                        -

                        printBox.offsetTop;


                    newWidth = clamp(

                        newWidth,

                        minimumSize,

                        maximumWidth

                    );


                    newHeight = clamp(

                        newHeight,

                        minimumSize,

                        maximumHeight

                    );


                    printBox.style.width =

                        newWidth + "px";


                    printBox.style.height =

                        newHeight + "px";


                    updateFieldsFromBox();

                }

            }

        );


        // =================================================
        // STOP DRAG / RESIZE
        // =================================================

        document.addEventListener(

            "pointerup",

            function () {

                dragging = false;

                resizing = false;

            }

        );


        // =================================================
        // MANUAL FIELD CHANGES
        //
        // Admin can still type values manually.
        // =================================================

        [

            xInput,

            yInput,

            widthInput,

            heightInput,

        ].forEach(

            function (
                input
            ) {

                input.addEventListener(

                    "input",

                    updateBoxFromFields

                );

            }

        );


        // =================================================
        // CENTER PRINT AREA
        // =================================================

        centerButton.addEventListener(

            "click",

            function () {

                let width =

                    numberValue(
                        widthInput,
                        50
                    );


                let height =

                    numberValue(
                        heightInput,
                        50
                    );


                width = clamp(

                    width,

                    1,

                    100

                );


                height = clamp(

                    height,

                    1,

                    100

                );


                const x =

                    (
                        100

                        -

                        width
                    )

                    /

                    2;


                const y =

                    (
                        100

                        -

                        height
                    )

                    /

                    2;


                xInput.value =
                    x.toFixed(2);

                yInput.value =
                    y.toFixed(2);


                updateBoxFromFields();

            }

        );


        // =================================================
        // RESET
        //
        // Default:
        //
        // X      = 25
        // Y      = 25
        // Width  = 50
        // Height = 50
        // =================================================

        resetButton.addEventListener(

            "click",

            function () {

                xInput.value =
                    "25.00";

                yInput.value =
                    "25.00";

                widthInput.value =
                    "50.00";

                heightInput.value =
                    "50.00";


                updateBoxFromFields();

            }

        );


        // =================================================
        // CUSTOMIZABLE ON/OFF
        // =================================================

        function updateEditorVisibility() {

            if (!customizableInput) {

                editor.style.display =
                    "";

                return;

            }


            if (
                customizableInput.checked
            ) {

                editor.style.display =
                    "";

            }

            else {

                editor.style.display =
                    "none";

            }

        }


        if (customizableInput) {

            customizableInput.addEventListener(

                "change",

                updateEditorVisibility

            );

        }


        // =================================================
        // INITIALIZE
        // =================================================

        loadExistingImage();

        updateBoxFromFields();

        updateEditorVisibility();


        // =================================================
        // WINDOW RESIZE
        //
        // Reapply percentage positioning.
        // =================================================

        window.addEventListener(

            "resize",

            function () {

                updateBoxFromFields();

            }

        );

    }

);