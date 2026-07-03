package com.emall.inventory.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.emall.inventory.entity.Inventory;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface InventoryMapper extends BaseMapper<Inventory> {

    @Update("UPDATE inventory SET stock = stock - #{quantity}, version = version + 1 " +
            "WHERE product_id = #{productId} AND stock >= #{quantity} AND version = #{version}")
    int deductStockWithOptimisticLock(@Param("productId") Long productId,
                                       @Param("quantity") Integer quantity,
                                       @Param("version") Integer version);

    @Update("UPDATE inventory SET stock = stock - #{quantity} " +
            "WHERE product_id = #{productId} AND stock >= #{quantity}")
    int deductStockWithPessimisticLock(@Param("productId") Long productId,
                                        @Param("quantity") Integer quantity);

    @Update("UPDATE inventory SET stock = stock + #{quantity}, version = version + 1 " +
            "WHERE product_id = #{productId}")
    int restoreStock(@Param("productId") Long productId,
                     @Param("quantity") Integer quantity);
}
