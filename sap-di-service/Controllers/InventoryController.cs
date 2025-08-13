using System;
using System.Web.Http;
using SAPbobsCOM;

namespace WmsSapDiService.Controllers
{
    public class InventoryController : ApiController
    {
        [HttpPost]
        public IHttpActionResult GoodReceipt(GoodReceiptRequest request)
        {
            try
            {
                Console.WriteLine($"=== WMS GOOD RECEIPT REQUEST ===");
                Console.WriteLine($"Warehouse: {request.Whs}");
                Console.WriteLine($"Reference: {request.Reference}");
                Console.WriteLine($"Lines count: {request.Lines?.Length ?? 0}");

                string server = Environment.GetEnvironmentVariable("SAP_DI_SERVER");
                string companyDB = Environment.GetEnvironmentVariable("SAP_COMPANY_DB");
                string username = Environment.GetEnvironmentVariable("SAP_USERNAME");
                string password = Environment.GetEnvironmentVariable("SAP_PASSWORD");

                if (string.IsNullOrEmpty(server) || string.IsNullOrEmpty(companyDB) || 
                    string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
                {
                    Console.WriteLine("ERROR: SAP connection parameters not properly configured!");
                    return Ok(new { ok = false, error = new { code = "CONFIG_ERROR", message = "SAP connection parameters not configured" } });
                }

                var connectionManager = SAPConnectionManager.GetInstance(server, companyDB, username, password, SAPbobsCOM.BoDataServerTypes.dst_MSSQL2016);
                var company = connectionManager.GetConnection(out string connectError);
                
                if (company == null || !company.Connected)
                {
                    Console.WriteLine($"❌ SAP connection failed: {connectError}");
                    return Ok(new { ok = false, error = new { code = "CONNECTION_ERROR", message = connectError } });
                }

                Console.WriteLine("✅ Successfully connected to SAP Business One");
                Console.WriteLine("Creating Good Receipt document in SAP...");

                var oGoodReceipt = (SAPbobsCOM.Documents)company.GetBusinessObject(SAPbobsCOM.BoObjectTypes.oInventoryGenEntry);
                
                oGoodReceipt.DocDate = DateTime.Now;
                oGoodReceipt.Comments = $"WMS Good Receipt: {request.Reference}";

                for (int i = 0; i < request.Lines.Length; i++)
                {
                    var line = request.Lines[i];
                    
                    if (i > 0)
                    {
                        oGoodReceipt.Lines.Add();
                        oGoodReceipt.Lines.SetCurrentLine(i);
                    }

                    oGoodReceipt.Lines.ItemCode = line.Item;
                    oGoodReceipt.Lines.Quantity = (double)line.Qty;
                    oGoodReceipt.Lines.WarehouseCode = request.Whs;

                    if (!string.IsNullOrEmpty(line.Lot))
                    {
                        var oItem = (SAPbobsCOM.Items)company.GetBusinessObject(SAPbobsCOM.BoObjectTypes.oItems);
                        if (oItem.GetByKey(line.Item))
                        {
                            if (oItem.ManageBatchNumbers == SAPbobsCOM.BoYesNoEnum.tYES)
                            {
                                oGoodReceipt.Lines.BatchNumbers.BatchNumber = line.Lot;
                                oGoodReceipt.Lines.BatchNumbers.Quantity = (double)line.Qty;
                                oGoodReceipt.Lines.BatchNumbers.Add();
                            }
                            else if (oItem.ManageSerialNumbers == SAPbobsCOM.BoYesNoEnum.tYES)
                            {
                                for (int s = 0; s < (int)line.Qty; s++)
                                {
                                    oGoodReceipt.Lines.SerialNumbers.InternalSerialNumber = $"{line.Lot}-{s + 1}";
                                    oGoodReceipt.Lines.SerialNumbers.Quantity = 1;
                                    oGoodReceipt.Lines.SerialNumbers.Add();
                                }
                            }
                        }
                    }
                }

                int retCode = oGoodReceipt.Add();
                if (retCode == 0)
                {
                    string docEntry = company.GetNewObjectKey();
                    Console.WriteLine($"✅ Good Receipt created successfully! DocEntry: {docEntry}");
                    return Ok(new { ok = true, data = new { docEntry = int.Parse(docEntry), docNum = docEntry } });
                }
                else
                {
                    company.GetLastError(out int errCode, out string errMsg);
                    Console.WriteLine($"❌ Good Receipt creation failed: Error {errCode}: {errMsg}");
                    return Ok(new { ok = false, error = new { code = errCode, message = errMsg } });
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception in Good Receipt creation: {ex.Message}");
                return Ok(new { ok = false, error = new { code = "EXCEPTION", message = ex.Message } });
            }
        }

        [HttpPost]
        public IHttpActionResult GoodIssue(GoodIssueRequest request)
        {
            try
            {
                Console.WriteLine($"=== WMS GOOD ISSUE REQUEST ===");
                Console.WriteLine($"Warehouse: {request.Whs}");
                Console.WriteLine($"Reference: {request.Reference}");
                Console.WriteLine($"Lines count: {request.Lines?.Length ?? 0}");

                string server = Environment.GetEnvironmentVariable("SAP_DI_SERVER");
                string companyDB = Environment.GetEnvironmentVariable("SAP_COMPANY_DB");
                string username = Environment.GetEnvironmentVariable("SAP_USERNAME");
                string password = Environment.GetEnvironmentVariable("SAP_PASSWORD");

                if (string.IsNullOrEmpty(server) || string.IsNullOrEmpty(companyDB) || 
                    string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
                {
                    Console.WriteLine("ERROR: SAP connection parameters not properly configured!");
                    return Ok(new { ok = false, error = new { code = "CONFIG_ERROR", message = "SAP connection parameters not configured" } });
                }

                var connectionManager = SAPConnectionManager.GetInstance(server, companyDB, username, password, SAPbobsCOM.BoDataServerTypes.dst_MSSQL2016);
                var company = connectionManager.GetConnection(out string connectError);
                
                if (company == null || !company.Connected)
                {
                    Console.WriteLine($"❌ SAP connection failed: {connectError}");
                    return Ok(new { ok = false, error = new { code = "CONNECTION_ERROR", message = connectError } });
                }

                Console.WriteLine("✅ Successfully connected to SAP Business One");
                Console.WriteLine("Creating Good Issue document in SAP...");

                var oGoodIssue = (SAPbobsCOM.Documents)company.GetBusinessObject(SAPbobsCOM.BoObjectTypes.oInventoryGenExit);
                
                oGoodIssue.DocDate = DateTime.Now;
                oGoodIssue.Comments = $"WMS Good Issue: {request.Reference}";

                for (int i = 0; i < request.Lines.Length; i++)
                {
                    var line = request.Lines[i];
                    
                    if (i > 0)
                    {
                        oGoodIssue.Lines.Add();
                        oGoodIssue.Lines.SetCurrentLine(i);
                    }

                    oGoodIssue.Lines.ItemCode = line.Item;
                    oGoodIssue.Lines.Quantity = (double)line.Qty;
                    oGoodIssue.Lines.WarehouseCode = request.Whs;

                    if (!string.IsNullOrEmpty(line.Lot))
                    {
                        var oItem = (SAPbobsCOM.Items)company.GetBusinessObject(SAPbobsCOM.BoObjectTypes.oItems);
                        if (oItem.GetByKey(line.Item))
                        {
                            if (oItem.ManageBatchNumbers == SAPbobsCOM.BoYesNoEnum.tYES)
                            {
                                oGoodIssue.Lines.BatchNumbers.BatchNumber = line.Lot;
                                oGoodIssue.Lines.BatchNumbers.Quantity = (double)line.Qty;
                                oGoodIssue.Lines.BatchNumbers.Add();
                            }
                            else if (oItem.ManageSerialNumbers == SAPbobsCOM.BoYesNoEnum.tYES)
                            {
                                for (int s = 0; s < (int)line.Qty; s++)
                                {
                                    oGoodIssue.Lines.SerialNumbers.InternalSerialNumber = $"{line.Lot}-{s + 1}";
                                    oGoodIssue.Lines.SerialNumbers.Quantity = 1;
                                    oGoodIssue.Lines.SerialNumbers.Add();
                                }
                            }
                        }
                    }
                }

                int retCode = oGoodIssue.Add();
                if (retCode == 0)
                {
                    string docEntry = company.GetNewObjectKey();
                    Console.WriteLine($"✅ Good Issue created successfully! DocEntry: {docEntry}");
                    return Ok(new { ok = true, data = new { docEntry = int.Parse(docEntry), docNum = docEntry } });
                }
                else
                {
                    company.GetLastError(out int errCode, out string errMsg);
                    Console.WriteLine($"❌ Good Issue creation failed: Error {errCode}: {errMsg}");
                    return Ok(new { ok = false, error = new { code = errCode, message = errMsg } });
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception in Good Issue creation: {ex.Message}");
                return Ok(new { ok = false, error = new { code = "EXCEPTION", message = ex.Message } });
            }
        }

        [HttpPost]
        public IHttpActionResult Transfer(TransferRequest request)
        {
            try
            {
                Console.WriteLine($"=== WMS INVENTORY TRANSFER REQUEST ===");
                Console.WriteLine($"From Warehouse: {request.FromWhs}");
                Console.WriteLine($"To Warehouse: {request.ToWhs}");
                Console.WriteLine($"Reference: {request.Reference}");
                Console.WriteLine($"Lines count: {request.Lines?.Length ?? 0}");

                string server = Environment.GetEnvironmentVariable("SAP_DI_SERVER");
                string companyDB = Environment.GetEnvironmentVariable("SAP_COMPANY_DB");
                string username = Environment.GetEnvironmentVariable("SAP_USERNAME");
                string password = Environment.GetEnvironmentVariable("SAP_PASSWORD");

                if (string.IsNullOrEmpty(server) || string.IsNullOrEmpty(companyDB) || 
                    string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
                {
                    Console.WriteLine("ERROR: SAP connection parameters not properly configured!");
                    return Ok(new { ok = false, error = new { code = "CONFIG_ERROR", message = "SAP connection parameters not configured" } });
                }

                var connectionManager = SAPConnectionManager.GetInstance(server, companyDB, username, password, SAPbobsCOM.BoDataServerTypes.dst_MSSQL2016);
                var company = connectionManager.GetConnection(out string connectError);
                
                if (company == null || !company.Connected)
                {
                    Console.WriteLine($"❌ SAP connection failed: {connectError}");
                    return Ok(new { ok = false, error = new { code = "CONNECTION_ERROR", message = connectError } });
                }

                Console.WriteLine("✅ Successfully connected to SAP Business One");
                Console.WriteLine("Creating Inventory Transfer document in SAP...");

                var oTransfer = (SAPbobsCOM.StockTransfer)company.GetBusinessObject(SAPbobsCOM.BoObjectTypes.oStockTransfer);
                
                oTransfer.DocDate = DateTime.Now;
                oTransfer.FromWarehouse = request.FromWhs;
                oTransfer.ToWarehouse = request.ToWhs;
                oTransfer.Comments = $"WMS Inventory Transfer: {request.Reference}";

                for (int i = 0; i < request.Lines.Length; i++)
                {
                    var line = request.Lines[i];
                    
                    if (i > 0)
                    {
                        oTransfer.Lines.Add();
                        oTransfer.Lines.SetCurrentLine(i);
                    }

                    oTransfer.Lines.ItemCode = line.Item;
                    oTransfer.Lines.Quantity = (double)line.Qty;
                    oTransfer.Lines.FromWarehouseCode = request.FromWhs;
                    oTransfer.Lines.WarehouseCode = request.ToWhs;

                    if (!string.IsNullOrEmpty(line.Lot))
                    {
                        var oItem = (SAPbobsCOM.Items)company.GetBusinessObject(SAPbobsCOM.BoObjectTypes.oItems);
                        if (oItem.GetByKey(line.Item))
                        {
                            if (oItem.ManageBatchNumbers == SAPbobsCOM.BoYesNoEnum.tYES)
                            {
                                oTransfer.Lines.BatchNumbers.BatchNumber = line.Lot;
                                oTransfer.Lines.BatchNumbers.Quantity = (double)line.Qty;
                                oTransfer.Lines.BatchNumbers.Add();
                            }
                            else if (oItem.ManageSerialNumbers == SAPbobsCOM.BoYesNoEnum.tYES)
                            {
                                for (int s = 0; s < (int)line.Qty; s++)
                                {
                                    oTransfer.Lines.SerialNumbers.InternalSerialNumber = $"{line.Lot}-{s + 1}";
                                    oTransfer.Lines.SerialNumbers.Quantity = 1;
                                    oTransfer.Lines.SerialNumbers.Add();
                                }
                            }
                        }
                    }
                }

                int retCode = oTransfer.Add();
                if (retCode == 0)
                {
                    string docEntry = company.GetNewObjectKey();
                    Console.WriteLine($"✅ Inventory Transfer created successfully! DocEntry: {docEntry}");
                    return Ok(new { ok = true, data = new { docEntry = int.Parse(docEntry), docNum = docEntry } });
                }
                else
                {
                    company.GetLastError(out int errCode, out string errMsg);
                    Console.WriteLine($"❌ Inventory Transfer creation failed: Error {errCode}: {errMsg}");
                    return Ok(new { ok = false, error = new { code = errCode, message = errMsg } });
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception in Inventory Transfer creation: {ex.Message}");
                return Ok(new { ok = false, error = new { code = "EXCEPTION", message = ex.Message } });
            }
        }
    }

    public class GoodReceiptRequest
    {
        public string Whs { get; set; }
        public string Reference { get; set; }
        public InventoryLine[] Lines { get; set; }
    }

    public class GoodIssueRequest
    {
        public string Whs { get; set; }
        public string Reference { get; set; }
        public InventoryLine[] Lines { get; set; }
    }

    public class TransferRequest
    {
        public string FromWhs { get; set; }
        public string ToWhs { get; set; }
        public string Reference { get; set; }
        public InventoryLine[] Lines { get; set; }
    }

    public class InventoryLine
    {
        public string Item { get; set; }
        public decimal Qty { get; set; }
        public string Lot { get; set; }
    }
}
