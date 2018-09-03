<p align="center">
  <img
    src="http://neonexchange.org/img/NEX-logo.svg"
    width="125px;">
    
</p>
<h3 align="center">NEX Token Smart Contract</h3>
<hr/>



#### Installation

Clone the repository and navigate into the project directory. 
Make a Python 3 virtual environment and activate it via

```shell
python3 -m venv venv
source venv/bin/activate
```

or to explicitly install Python 3.6 via

    virtualenv -p /usr/local/bin/python3.6 venv
    source venv/bin/activate

Then install the requirements via

```shell
(venv) pip install -r requirements.txt
```

#### Compilation / Build

- Manual
    The template may be manually compiled from the Python shell as follows
    
    ```python
    from boa.compiler import Compiler
    
    Compiler.load_and_save('NEX.py')
    ```
    
    This will compile your template to `NEX.avm`

- From neo-python
    
    ```neo-python
    neo> build ../nex-token/NEX.py test 0710 07 True False True name []                                                                                   
    [I 180831 11:04:58 BuildNRun:50] Saved output to ../nex-token/NEX.avm 
    [I 180831 11:05:17 Invoke:586] Used 0.15 Gas 
    
    -----------------------------------------------------------
    Calling ../nex-token/NEX.py with arguments ['[]', 'name'] 
    Test deploy invoke successful
    Used total of 242 operations 
    Result [{'type': 'String', 'value': 'NEX Token'}] 
    Invoke TX gas cost: 0.0001 
    -------------------------------------------------------------    
    ```

#### Bug Reporting

Please contact us at bugbounty@neonexchange.org if you find something you believe we should know about.
