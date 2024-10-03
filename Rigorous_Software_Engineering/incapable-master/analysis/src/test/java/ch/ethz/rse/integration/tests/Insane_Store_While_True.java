
package ch.ethz.rse.integration.tests;
// DISABLED
import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class Insane_Store_While_True {
  public static void m1(){
    
    Store s = new Store(2, 10);
    while(true){
      s.get_delivery(1);
    }
    
   }
 }

