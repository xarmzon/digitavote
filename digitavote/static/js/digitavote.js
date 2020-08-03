window.onload = function(){
    var phone = document.getElementById("phone")
    var form = document.getElementById("form");
    if (form){
        if(phone){
            phone.setAttribute("data-pristine-pattern-message", "Please enter a valid Nigeria phone number")
        }
        validateForm(form);
    }
    toastr.options = {
        "closeButton": true,
        "newestOnTop": true,
        "progressBar": true,
        "positionClass": "toast-bottom-left",
        "timeOut": "8000",
        "extendedTimeOut": "10000",
        "showEasing": "swing",
        "hidedEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut",
        "preventDuplicates": true,
    };

    var table_ = $("#list-table");
 
    if(Object.keys(table_).length !== 0){
        table_.DataTable({
            ordering: false,
            dom: 'Bfrtip',
            buttons: [
                'csvHtml5', 
                'excelHtml5', 
                'pdfHtml5'
            ],
        });
    }
};

/*form validation*/
function validateForm(form){
    
    var config = {
        classTo: 'form-group',
        errorClass: 'has-danger',
        successClass: 'has-success',
        errorTextParent: 'form-group',
        errorTextTag: 'div',
        errorTextClass: 'text-help text-danger'
    };
    var pristine = new Pristine(form,config);
    form.addEventListener('submit', function(e){
        e.preventDefault();
        var valid = pristine.validate();
        if (valid){
            e.currentTarget.submit();
        }
    });
    cpassword = document.getElementById("cpassword");
    if(cpassword){
        password = document.getElementById("password");
        pristine.addValidator(cpassword, (value)=>{
                if(value !== password.value){
                    return false;
                }else{
                    return true;
                }
        },"The password mismatch", 2, false);
    }
}
/*Photo Upload*/
var img_box = document.getElementById("photo")
if(img_box){
    img_box.addEventListener('click', ()=>{
        $("#photo-file").trigger('click');
    });
    var max_limit = 1024 * 50; //50kb
    var allow_types = ["image/jpg", "image/jpeg", "image/png"]
    var ifile = document.getElementById("photo-file");
    ifile.addEventListener('change', ()=>{
        
        var img = ifile.files[0];
        if(!allow_types.includes(img.type)){
            toastr.error('Error: Only jpg/jpeg/png are allowed.');
        }else if(img.size > max_limit){
            toastr.error('Error: maximum size is ' + max_limit / 1024 +'kb')
        }else{
            var form = document.getElementById("photo-form");
            form.submit();
        }
    });
}

/*Upload Bulk Voters */
$("#voter-bulk-upload").click(()=> $("#voter-file").trigger('click'));
$("#voter-file").change(()=>{
    var max_limit = 1024 * 1024 * 2; //2mb
    var allow_ext = ["csv", "xlsx"]
    var ifile = document.getElementById("voter-file").files[0];
    var file_ext = ifile.name.split(".").pop().toLowerCase();
    if(!allow_ext.includes(file_ext)){
        toastr.error('Error: Only CSV/XLSX files are allowed.');
    }else if(ifile.size > max_limit){
        toastr.error('Error: maximum size is ' + max_limit / (1024 * 1024) +'mb')
    }else{
        var form = document.getElementById("voters-upload-form");
        form.submit();
    }
});
